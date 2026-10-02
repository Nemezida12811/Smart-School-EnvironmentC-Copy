import uos

from lib.constants import LOG_FILE

DEBUG = 1
INFO = 2
WARNING = 3
ERROR = 4
CRITICAL = 5

LOG_LEVEL = DEBUG

def main(lvl, tag, message):
    if lvl >= LOG_LEVEL:
        print(f"[-{tag}-]{message}")
        
    if lvl > INFO:
        #TODO: time
        log_message = f"[-{tag}-]{message}\n"
        
        try:
            try:
                f_size = uos.stat(LOG_FILE)[6]
            except OSError:
                f_size = 0

            if f_size > 2000:
                with open(LOG_FILE, "r") as f:
                    f.seek(500)
                    content = f.read()
                    correct_start = content.find('\n')
                    if correct_start != -1:
                        content = content[correct_start + 1:]
                
                with open(LOG_FILE, "w") as f:
                    f.write(content)

            with open(LOG_FILE, "a") as file:
                file.write(log_message)
        except OSError:
            pass
        

def debug(message):
    main(DEBUG, "DEBUG", message)


def info(message):
    main(INFO, "INFO", message)


def warning(message):
    main(WARNING, "WARNING", message)


def error(message):
    main(ERROR, "ERROR", message)


def critical(message):
    main(CRITICAL, "CRITICAL", message)