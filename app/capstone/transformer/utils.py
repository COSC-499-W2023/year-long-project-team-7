import traceback
from django.conf import settings


def error(e: Exception) -> None:
    path = f"{settings.BASE_DIR}/loggo.txt"

    with open(path, "a") as log_file:
        log_file.write("\n\n\n")
        traceback.print_exc(file=log_file)
        log_file.flush()

    traceback.print_exc()
