import time

from libs.chrome import Chrome

if __name__ == '__main__':
    Chrome.run_background()
    time.sleep(1)
    Chrome.close()
