#!/usr/bin/env python3

import argparse
import glob
import json
import os

# Output: .properties file for triggering build_sanity_matrix
# (if .properties file is absent, no need to trigger)
# Properties:
#   CURRENT_BUILD_NUMBER (the build number for which to run sanity)
#   VERSION
#   DISTROS - whitespace-separated list of platforms (debian8, ubuntu14.04...)

# QQQ The set of platforms for a given release should come from a
# canonical location, such as product-config.json, or perhaps the
# build database. For now we keep the version-specific platform lists
# here.
# For now these 'platform' keys are the letters in the installer filenames.
# The boolean value is whether that platform is passed on to
# build_sanity_matrix (ie, put into the .properties file).
PLAT_LISTS = {
    "5.0.0": {
        "centos6": False,
        "centos7": True,
        "debian7": False,
        "debian8": True,
        "macos": True,
        "suse11": True,
        "suse12": False,
        "ubuntu14.04": True,
        "ubuntu16.04": False,
        "windows": True,
    },
    "5.0.1": {
        "centos6": False,
        "centos7": True,
        "debian7": False,
        "debian8": True,
        "macos": True,
        "suse11": True,
        "suse12": False,
        "ubuntu14.04": True,
        "ubuntu16.04": False,
        "windows": True,
    },
    "5.1.0": {
        "centos6": False,
        "centos7": True,
        "debian8": True,
        "debian9": False,
        "macos": True,
        "suse11": True,
        "suse12": False,
        "ubuntu14.04": True,
        "ubuntu16.04": False,
        "windows": True,
    },
}

LAST_SANITY_FILENAME="/latestbuilds/last-sanity.json"
TRIGGER_PROPERTIES_FILENAME="build-sanity-trigger.properties"

class SanityTrigger:
    """
    For a given version, looks for the most recent build that is
    complete (all installers exist).
    """

    def __init__(self, product, version):
        self.version = version
        self.product = product
        self.ver_dir = os.path.join("/latestbuilds", product, version)
        self.plats = PLAT_LISTS[version]
        self.bld_num = 0
        self.last_bld = 0

    def get_last_sanity(self):
        """
        Read the global "last-sanity" JSON file and set self.last_bld
        for the current version. Return "0" if information cannot be found,
        either because the file is missing, the product is missing, or
        the version is missing.
        """
        # QQQ in future, get/set_last_sanity() functions should be
        # replaced with equivalent functions backed by the build database
        if not os.path.exists(LAST_SANITY_FILENAME):
            self.sanity = {}
        else:
            with open(LAST_SANITY_FILENAME) as sanity_file:
                self.sanity = json.load(sanity_file)

        if self.product in self.sanity:
            product = self.sanity[self.product]
            if self.version in product:
                self.last_bld = product[self.version]

        return self.last_bld

    def set_last_sanity(self, bld_num):
        """
        Updates the global last-sanity JSON file with a new build number
        for the current product and version. Creates file if necessary.
        Expected that get_last_sanity() has been called to initialize
        self.sanity.
        """
        if not self.product in self.sanity:
            self.sanity[self.product] = {}
        self.bld_num = bld_num
        self.sanity[self.product][self.version] = bld_num
        with open(LAST_SANITY_FILENAME, "w") as sanity_file:
            json.dump(self.sanity, sanity_file, indent=4,
                sort_keys=True, separators=(',', ': '))

    def check_build(self, bld_num):
        """
        Checks a specific build number for completeness
        """
        # QQQ In future this should be replaced with a query to the
        # build database
        bld_dir = os.path.join(self.ver_dir, str(bld_num))
        for plat in self.plats.keys():
            # QQQ Assumes format of filename unique to couchbase-server
            files = glob.glob("{}/couchbase-server-enterprise?{}*{}*".format(
                bld_dir, self.version, plat
            ))
            files = [x for x in files if not (x.endswith(".md5") or x.endswith(".sha256"))]
            if len(files) == 0:
                return False
        return True

    def get_latest_build(self):
        """
        Walk latestbuilds to find the newest complete build that is
        newer than self.last_bld. If none are, returns self.last_bld.
        """
        # Retrieve last sanity-checked build number (could be 0)
        self.get_last_sanity()

        # List all build numbers for this version. Note this may include
        # builds for other versions, since all versions for a given
        # release share a build directory.
        builds = [int(x) for x in os.listdir(self.ver_dir)
            if x.isdigit() and int(x) > self.last_bld]
        builds.sort()

        # Check each build after last sanity-checked build
        bld_num = self.last_bld
        for build in builds:
            print ("Checking build " + str(build))
            if self.check_build(build):
                bld_num = build
        print("bld_num is now " + str(bld_num))
        return bld_num

    def write_properties(self, prop_filename):
        """
        Writes out a build-sanity-trigger.properties file with
        appropriate trigger information.
        """
        sanity_plats = [x for x in self.plats.keys() if self.plats[x]]
        with open(prop_filename, "w") as prop:
            prop.write("CURRENT_BUILD_NUMBER={}\n".format(self.bld_num))
            prop.write("VERSION={}\n".format(self.version))
            prop.write("DISTROS={}".format(" ".join(sanity_plats)))

def main():
    """
    Parse the command line and execute job
    """
    parser = argparse.ArgumentParser(
        description = "Find latest successful build for given product/version"
    )
    parser.add_argument('--product', default="couchbase-server",
        help="Product name")
    parser.add_argument('--version', required=True, help="Version number")

    args = parser.parse_args()

    trigger = SanityTrigger(args.product, args.version)

    last_bld = trigger.get_last_sanity()
    bld_num = trigger.get_latest_build()
    if bld_num > last_bld:
        print ("Writing " + TRIGGER_PROPERTIES_FILENAME)
        trigger.set_last_sanity(bld_num)
        trigger.write_properties(TRIGGER_PROPERTIES_FILENAME)
    else:
        print ("Nothing to do; not writing " + TRIGGER_PROPERTIES_FILENAME)
        if (os.path.exists(TRIGGER_PROPERTIES_FILENAME)):
            os.unlink(TRIGGER_PROPERTIES_FILENAME)

if __name__ == '__main__':
    main()
