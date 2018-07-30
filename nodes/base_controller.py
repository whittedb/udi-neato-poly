import polyinterface
import logging
import json
from copy import deepcopy

LOGGER = polyinterface.LOGGER

DEFAULT_DEBUG_MODE = 0


class BaseController(polyinterface.Controller):
    def __init__(self, polyglot):
        self.debug_mode = DEFAULT_DEBUG_MODE
        self.profile_info = None
        self.server_data = self.get_server_data()
        super().__init__(polyglot)
        self.primary = self.address

    def start(self):
        self.check_profile()
        self.setDriver("GV1", self.server_data["version_major"])
        self.setDriver("GV2", self.server_data["version_minor"])
        self.set_debug_mode(self.getCustomParam("debugMode"))
        self.setDriver("ST", 1)

    def discover(self, *args, **kwargs):
        pass

    def set_debug_mode(self, level):
        if level is None:
            level = 0
        else:
            level = int(level)
        self.debug_mode = level
        self.addCustomParam({"debugMode": self.debug_mode})
        self.setDriver("GV5", level)
        # 0=All 10=Debug are the same because 0 (NOTSET) doesn't show everything.
        if level == 0 or level == 10:
            self.set_all_logs(logging.DEBUG)
        elif level == 20:
            self.set_all_logs(logging.INFO)
        elif level == 30:
            self.set_all_logs(logging.WARNING)
        elif level == 40:
            self.set_all_logs(logging.ERROR)
        elif level == 50:
            self.set_all_logs(logging.CRITICAL)
        else:
            self.l_error("set_debug_level", "Unknown level {0}".format(level))

    @classmethod
    def set_all_logs(cls, level):
        LOGGER.setLevel(level)
#        logging.getLogger("urllib3").setLevel(level)

    def get_server_data(self):
        # Read the SERVER info from the json.
        try:
            with open('server.json') as data:
                server_data = json.load(data)
        except Exception as err:
            self.l_error("get_server_data", "ailed to read server file {0}: {1}".format(
                    "server.json", err), exc_info=True)
            return False
        data.close()
        # Get the version info
        try:
            version = server_data["credits"][0]["version"]
        except (KeyError, ValueError):
            self.l_info("get_server_data", "Version not found in server.json.")
            version = '0.0.0'
        # Split version into two floats.
        sv = version.split(".")
        v1 = 0
        v2 = 0
        if len(sv) > 0:
            v1 = int(sv[0])
            if len(sv) > 1:
                v2 = int(sv[2])
        server_data["version"] = version
        server_data["version_major"] = v1
        server_data["version_minor"] = v2
        return server_data

    def get_profile_info(self):
        pvf = "profile/version.txt"
        try:
            with open(pvf) as f:
                pv = f.read().replace("\n", "")
        except Exception as err:
            self.l_error("get_profile_info", "Failed to read  file {0}: {1}".format(pvf, err), exc_info=True)
            pv = 0
        return {"version": pv}

    def check_profile(self):
        self.profile_info = self.get_profile_info()

        # Set Default profile version if not Found
        cd = deepcopy(self.polyConfig["customData"])
        self.l_info("check_profile", "profile_info={0} customData={1}".format(self.profile_info, cd))
        if "profile_info" not in cd:
            cd["profile_info"] = {"version": 0}
        if self.profile_info["version"] == cd["profile_info"]["version"]:
            update_profile = False
        else:
            update_profile = True
            self.poly.installprofile()
        self.l_info("check_profile", "update_profile={}".format(update_profile))
        cd["profile_info"] = self.profile_info
        self.saveCustomData(cd)

    """
    Command Functions
    """
    def cmd_install_profile(self, command):
        self.l_info("cmd_install_profile:", "Profile update requested")
        st = self.poly.installprofile()
        return st

    def cmd_set_debug_mode(self, command):
        val = command.get("value")
        self.l_info("cmd_set_debug_mode", val)
        self.set_debug_mode(val)

    def l_info(self, name, string):
        LOGGER.info("%s:%s: %s" % (self.id, name, string))

    def l_error(self, name, string, exc_info=False):
        LOGGER.error("%s:%s: %s" % (self.id, name, string), exc_info=exc_info)

    def l_warning(self, name, string):
        LOGGER.warning("%s:%s: %s" % (self.id, name, string))

    def l_debug(self, name, string):
        LOGGER.debug("%s:%s: %s" % (self.id, name, string))

    """
    Optional.
    Since the controller is the parent node in ISY, it will actual show up as a node.
    So it needs to know the drivers and what id it will use. The drivers are
    the defaults in the parent Class, so you don't need them unless you want to add to
    them. The ST and GV1 variables are for reporting status through Polyglot to ISY,
    DO NOT remove them. UOM 2 is boolean.

    Override and/or append to these as required
    """
    id = "baseController"
    commands = {
        "SET_DM": cmd_set_debug_mode,
        "DISCOVER": discover,
        "UPDATE_PROFILE": cmd_install_profile
    }
    drivers = [
        {"driver": "ST", "value": 0, "uom": 2},
        {"driver": "GV1", "value": 0, "uom": 56},   # vmaj: Version Major
        {"driver": "GV2", "value": 0, "uom": 56},   # vmin: Version Minor
        {"driver": "GV3", "value": DEFAULT_DEBUG_MODE, "uom": 25}    # Debug (Log) Mode
    ]
