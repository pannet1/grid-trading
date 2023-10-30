from toolkit.telegram import Telegram
from toolkit.fileutils import Fileutils

dir = "../../"
config = Fileutils().get_lst_fm_yml(dir + "config2.yaml")
print(config)
bot_function = Telegram(config[1]["telegram"])
bot_function.send_msg({"message": "hello"})
