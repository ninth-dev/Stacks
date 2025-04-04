import sublime
import sublime_plugin
from typing import Optional, Any, Dict
import json
from Stacks.components.Common import _get_window_state, _close_open_views, _loaded_stack_name_settings_key
from Stacks.StacksCommand import StacksCommand
from Stacks.components.FileUtils import SaveError, LoadError, save_stack_file, load_stack_file
from Stacks.components.Files import StackFileName
from Stacks.components.ResultTypes import Either
from logging import Logger

class StacksCreateCommand(StacksCommand):

  def on_run(self, window: sublime.Window, logger: Logger, stack_file: StackFileName):
    window.show_input_panel(
      caption = "Stack name",
      on_done = lambda sn: self.on_stack_name(window, stack_file, sn),
      initial_text = "",
      on_change = None,
      on_cancel = None
    )

  def on_stack_name(self, window: sublime.Window, stack_file: StackFileName, stack_name: str) -> None:
    # TODO: Merge with existing values
    # TODO: if name is already taken prompt for overwrite confirmation?
    load_result: Either[LoadError, Dict[str, Any]] = load_stack_file(stack_file)

    # We need to know if this is a rename or direct save
    stacks_to_save: Dict[str, Any] = load_result.value() if load_result.has_value() else {}
    views_to_save = _get_window_state(window)

    stacks_to_save.update({ stack_name : views_to_save})
    new_stack_json_content: str = json.dumps(stacks_to_save)
    save_result: Either[SaveError, None] = save_stack_file(stack_file, new_stack_json_content)
    if save_result.has_value():
      close_all_windows = sublime.yes_no_cancel_dialog("Close all windows?")
      if close_all_windows == sublime.DIALOG_YES:
        # TODO: Do we need to move this option to config?
        _close_open_views(window)
        # Remove stack name of save and close
        window.settings().erase(_loaded_stack_name_settings_key)
      else:
        # Set stack name on save and leave open
        window.settings().update({_loaded_stack_name_settings_key : stack_name})
        view = window.active_view()
        if view:
          view.show_popup(f"<h1>Saved stack: {stack_name}<h1>", max_width=640, max_height=480)
    else:
      error: SaveError = save_result.error()
      sublime.message_dialog(f"Could not save stack.\nError:\n{str(error.value)}")
