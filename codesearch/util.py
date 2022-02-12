COL_PINK = "\033[95m"
COL_OKBLUE = "\033[94m"
COL_OKGREEN = "\033[92m"
COL_WARNING = "\033[93m"
COL_FAIL = "\033[91m"
COL_ENDC = "\033[0m"


def cmd_colgen(col: str):
    def cmd_out(text):
        return f"{col}{text}{COL_ENDC}"

    return cmd_out


cmd_green = cmd_colgen(COL_OKGREEN)
cmd_yellow = cmd_colgen(COL_WARNING)
