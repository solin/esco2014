import os
import code

class FEMTECConsole(code.InteractiveConsole):
    """An interactive console with readline support. """

    def __init__(self):
        code.InteractiveConsole.__init__(self)

        try:
            import readline
        except ImportError:
            pass
        else:
            import os
            import atexit

            readline.parse_and_bind('tab: complete')

            if hasattr(readline, 'read_history_file'):
                history = os.path.expanduser('~/.femtec-history')

                try:
                    readline.read_history_file(history)
                except IOError:
                    pass

                atexit.register(readline.write_history_file, history)

console = FEMTECConsole()
console.interact()
