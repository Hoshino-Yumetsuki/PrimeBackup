from abc import ABC
from typing import Any

from mcdreforged.api.all import *

from prime_backup.action.operate_backup_tag_action import SetBackupTagAction, ClearBackupTagAction
from prime_backup.mcdr.task.basic_task import OperationTask
from prime_backup.mcdr.text_components import TextComponents
from prime_backup.types.backup_tags import BackupTagName


class _OperateBackupTagTaskBase(OperationTask, ABC):
	def __init__(self, source: CommandSource, backup_id: int, tag_name: BackupTagName):
		super().__init__(source)
		self.backup_id = backup_id
		self.tag_name = tag_name


class SetBackupTagTask(_OperateBackupTagTaskBase):
	def __init__(self, source: CommandSource, backup_id: int, tag_name: BackupTagName, value: Any):
		super().__init__(source, backup_id, tag_name)
		self.value = value

	@property
	def name(self) -> str:
		return 'set_tag'

	def run(self) -> None:
		SetBackupTagAction(self.backup_id, self.tag_name, self.value).run()
		self.reply(self.tr('set', TextComponents.backup_id(self.backup_id), TextComponents.tag_name(self.tag_name), TextComponents.auto(self.value)))


class ClearBackupTagTask(_OperateBackupTagTaskBase):
	@property
	def name(self) -> str:
		return 'clear_tag'

	def run(self) -> None:
		ok = ClearBackupTagAction(self.backup_id, self.tag_name).run()
		if ok:
			self.reply(self.tr('cleared', TextComponents.backup_id(self.backup_id), TextComponents.tag_name(self.tag_name)))
		else:
			self.reply(self.tr('not_exists', TextComponents.backup_id(self.backup_id), TextComponents.tag_name(self.tag_name)))