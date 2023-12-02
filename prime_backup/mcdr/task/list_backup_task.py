import contextlib
import copy
import json
import threading

from mcdreforged.api.all import *

from prime_backup.action.count_backup_action import CountBackupAction
from prime_backup.action.get_backup_action import GetBackupAction
from prime_backup.action.list_backup_action import ListBackupIdAction
from prime_backup.exceptions import BackupNotFound
from prime_backup.mcdr.task import ReaderTask, TaskEvent
from prime_backup.mcdr.text_components import TextComponents
from prime_backup.types.backup_filter import BackupFilter
from prime_backup.utils import conversion_utils
from prime_backup.utils.mcdr_utils import mkcmd


class ListBackupTask(ReaderTask):
	def __init__(self, source: CommandSource, per_page: int, page: int, backup_filter: BackupFilter, show_size: bool):
		super().__init__(source)
		self.source = source
		self.backup_filter = copy.copy(backup_filter)
		self.per_page = per_page
		self.page = page
		self.is_aborted = threading.Event()
		self.show_size = show_size

	@property
	def name(self) -> str:
		return 'list'

	def is_abort_able(self) -> bool:
		return True

	def __make_command(self, page: int) -> str:
		def date_str(ts_ns: int) -> str:
			return json.dumps(conversion_utils.timestamp_to_local_date(ts_ns, decimal=ts_ns % 1000 != 0), ensure_ascii=False)

		cmd = mkcmd(f'list {page} --per-page {self.per_page}')
		if self.backup_filter.author is not None:
			cmd += f' --author {self.backup_filter.author}'
		if self.backup_filter.timestamp_start is not None:
			cmd += f' --start {date_str(self.backup_filter.timestamp_start)}'
		if self.backup_filter.timestamp_end is not None:
			cmd += f' --end {date_str(self.backup_filter.timestamp_end)}'
		if self.backup_filter.hidden is True:
			cmd += f' --show-hidden'

		return cmd

	def run(self):
		total_count = CountBackupAction(self.backup_filter).run()
		backup_ids = ListBackupIdAction(self.backup_filter, self.per_page, (self.page - 1) * self.per_page).run()

		self.reply(RTextList(
			RText('======== ', RColor.gray),
			self.tr('title', TextComponents.number(total_count)),
			RText(' ========', RColor.gray),
		))
		for backup_id in backup_ids:
			if self.is_aborted.is_set():
				self.reply(self.tr('aborted'))
				return
			with contextlib.suppress(BackupNotFound):
				backup = GetBackupAction(backup_id, calc_size=self.show_size).run()
				self.reply(TextComponents.backup_full(backup, True, show_size=self.show_size))

		max_page = max(0, (total_count - 1) // self.per_page + 1)
		t_prev = RText('<-')
		if 1 <= self.page - 1 <= max_page:  # has prev
			t_prev.h(self.tr('prev')).c(RAction.run_command, self.__make_command(self.page - 1))
		else:
			t_prev.set_color(RColor.dark_gray)
		t_next = RText('->')
		if 1 <= self.page + 1 <= max_page:  # has next
			t_next.h(self.tr('next')).c(RAction.run_command, self.__make_command(self.page + 1))
		else:
			t_next.set_color(RColor.dark_gray)
		self.reply(RTextList(t_prev, ' ', TextComponents.number(self.page), '/', TextComponents.number(max_page), ' ', t_next))

	def on_event(self, event: TaskEvent):
		if event in [TaskEvent.plugin_unload, TaskEvent.operation_aborted]:
			self.is_aborted.set()
