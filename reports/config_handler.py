import localconfig
import logging

#  think about handling errors in getting values from incorrect config
#  how our system must work in that situation?
#  at least log it and raise

logger = logging.getLogger("Worker.ConfigHandler")


class ConfigHandler(object):
    """
    Object that handle all things about config and how to read it
    The main idea that we may have parse fields in config in some interesting way
    And its better to do in one place - here
    """
    def __init__(
            self,
            config_path: str
    ):
        try:
            self.config_path = config_path
            self.config = localconfig.config
            self.config.read(self.config_path)
        except Exception as e:
            logger.critical("Error while reading config: {}".format(e))
            raise

        logger.debug("Start parsing file and creating config object")
        for section in self.config:
            # lets create a dict for all section content
            logger.debug("Creating section {}".format(section))
            sect_dict = dict()
            for key, value in self.config.items(section):
                # add values from section to dict
                sect_dict[key] = value
                # print(key, value, type(value))
            setattr(self, section, sect_dict)


        # then we need to parse some them in correct way
        # lets transform string to list
        adj_section = getattr(self, 'control_system')

        df_str = adj_section["data_fields"]
        df_list = df_str.split(' ')
        adj_section["data_fields"] = df_list

        # adj_section = getattr(self, 'adjustment')
        dfs_str = adj_section["search_log_fields"]
        dfs_list = dfs_str.split(' ')
        adj_section["search_log_fields"] = dfs_list

    def get_value(self, section: str, name: str):
        try:
            dict_ = getattr(self, section)
            return dict_[name]
        except Exception as e:
            logger.critical("Error while getting {} from section {}, {}".format(name, section, e))
            raise

    def get_section(self, section: str):
        try:
            return getattr(self, section)
        except Exception as e:
            logger.critical("Error while getting section {}, {}".format(section, e))
            raise


if __name__ == "__main__":
    ch = ConfigHandler(config_path='../worker.conf')
    # print(ch.__dict__)
    print(ch.get_section('led_unit'))
    print(ch.get_section('adjustment'))
    print(ch.get_value('adjustment', 'ppmv_to_mgco2'))
    print(ch.get_value('control_system', 'data_fields'))

    # print(ch.config)
    # print(ch.calibration_time)