from commity.utils import spinner as spinner_module


def test_spinner_uses_live_status(mocker):
    console = mocker.patch.object(spinner_module, "console")

    with spinner_module.spinner("Generating commit message..."):
        pass

    console.status.assert_called_once_with("Generating commit message...", spinner="dots12")


def test_spinner_console_forces_terminal_rendering():
    assert spinner_module.console.is_terminal
