import colorama, sys, os, time

class NatsumeUtils:
    def __init__(self):
        self.CCYAN = colorama.Fore.CYAN
        self.CRED = colorama.Fore.RED
        self.CMAGENTA = colorama.Fore.MAGENTA
        self.CRESET = colorama.Style.RESET_ALL

    def printError(self, module, msg):
        sys.stdout.write("{}[{}] {}{}".format(
            self.CRED, module, msg, self.CRESET
        ))
