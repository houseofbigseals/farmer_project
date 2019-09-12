import localconfig


class ConfigHandler(object):
    """
    Object that handle all things about config and how to read it
    The main idea that we may have parse fields in config in some interesting way
    And its better to do in one place - here
    """
    def __init__(
            self,
            config_path: str = '../worker.conf'
    ):
        self.config_path = config_path
        self.config = localconfig.config
        self.config.read(self.config_path)
        # TODO add here some try-except or smth and logging

        # print little information about config
        for section in self.config:
            print("\n")
            print(section)
            for key, value in self.config.items(section):
                print(key, value, type(value))

        # after initial check we have to read values from config,
        # parse them in correct way and add comments
        # comments must be here, not in .conf file

        # start read adjustment section
        self.volume = self.config.get('adjustment', 'volume')
        # fitotrone volume in m3
        self.raw_to_dry = self.config.get('adjustment', 'raw_to_dry')
        # conversion factor from raw plants weight to dry weight
        self.ppmv_to_mgCO2 = self.config.get('adjustment', 'ppmv_to_mgCO2')
        # conversion factor from ppmv CO2 to mgCO2/m3
        self.surface = self.config.get('adjustment', 'surface')
        # in m2 - surface of lighted crops
        self.surface_to_volume = self.config.get('adjustment', 'surface_to_volume')
        # in m3/m2
        self.mg_CO2_to_kg_dry_mass = self.config.get('adjustment', 'mg_CO2_to_kg_dry_mass')
        # in kg of dry mass / mg CO2 assimilated
        self.mg_CO2_to_kg_raw_mass = self.config.get('adjustment', 'mg_CO2_to_kg_raw_mass')
        # in kg of dry mass / mg CO2 assimilated
        # when water coefficient is 0.08
        self.ppfd_to_kW = self.config.get('adjustment', 'ppfd_to_kW')
        # kW / (mkmol/m2*sec)
        self.price_of_volume = self.config.get('adjustment', 'price_of_volume')
        # kg_of_equiv_mass / m3
        self.price_of_power = self.config.get('adjustment', 'price_of_power')
        # kg_of_equiv_mass / kW

        # TODO: add here unstable constants from I mA to ppfd conversion for leds

        # asdasd


if __name__ == "__main__":
    ch = ConfigHandler()
    # print(ch.config)
    # print(ch.calibration_time)