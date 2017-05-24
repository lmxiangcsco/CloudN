__author__ = 'lmxiang'

import logging
import unittest

from selenium import webdriver

from GUI import JoinCloudNVPC
from GUI import ViewLicenses
from tests.utils.vnet_utils import *
from tests.utils.vpc_utils import modify_ip_route


class JoinCloudNVNetTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Firefox()
        cls.driver.maximize_window()
        cls.logger = logging.getLogger("cloudn-test.tests.join_cloudn_vnet_tests")

    def test_join_cloudn_vnet(self):
        from tests.main import variables as _variables
        driver = self.driver
        cloud_type = "azure"
        vnet_name = "vnet-cloudn---10-100-0-3"
        vnet_id = "CN-284e1cea"
        cidr_block = "10.100.11.0/24"
        instance_subnet = "10.100.11.0"
        instance_mask = "255.255.255.0"
        vnet_region = "West US"
        inst_info = []

        try:
            # check the number of license already allocated before joining cloudn-test VNet
            lic_view = ViewLicenses(driver, login_required=True)
            lic_num1 = lic_view.view_allocated_license()
            self.logger.info("%d licenses allocated before joining cloudn-test VNet", lic_num1)

            join_cloudn_vnet = JoinCloudNVPC(driver)

            self.logger.info("Create a user instance in cloudn-test VNet ...")
            if create_user_instance(self.logger, vnet_name, vnet_id, "West US", "ExtraSmall", inst_info):
                self.logger.info("Successfully create a user instance in cloudn-test VNet.")
            else:
                self.logger.error("Failed to create a user instance in cloudn-test VNet. Abort.")
                return False

            self.logger.info("Waiting for joining cloudn-test VNet ...")
            self.assertTrue(join_cloudn_vnet.join_cloudn_vpc(cloud_type, vnet_name, cidr_block, vnet_region))

            self.logger.info("Allow subnet for joined cloudn-test VNet ...")
            self.assertTrue(join_cloudn_vnet.allow_subnet(vnet_name))

            self.logger.info("Add a route in local instance to access cloudn-test VNet instance ...")
            modify_ip_route(self.logger, "add", instance_subnet, instance_mask, _variables["cloudn_ip"], "eth0")

            # Ping the user instance to test the tunnel connection
            self.logger.info("Ping the user instance to test the tunnel connection ...")
            self.assertTrue(vpn_ping_user_instance(self.logger, vnet_name,
                                                   _variables["cloudn_instance_ip"],
                                                   _variables["cloudn_instance_username"],
                                                   _variables["cloudn_instance_password"],
                                                   inst_info))

            self.logger.info("Remove the route in local instance for accessing cloudn-test VNet instance ...")
            modify_ip_route(self.logger, "del", instance_subnet, instance_mask, _variables["cloudn_ip"], "eth0")

            join_cloudn_vnet = JoinCloudNVPC(driver)

            self.logger.info("Delete subnet for joined cloudn-test VNet ...")
            self.assertTrue(join_cloudn_vnet.delete_subnet(vnet_name))

            # check the number of licenses allocated after joining legacy VNet
            lic_view = ViewLicenses(driver)
            lic_num2 = lic_view.view_allocated_license()
            self.logger.info("%d licenses allocated after joining cloudn-test VNet", lic_num2)
            if lic_num2 - lic_num1 == 1:
                self.logger.info("License allocated properly after joining cloudn-test VNet")
                self.assertTrue(True)
            else:
                self.logger.error("License allocation is wrong after joining cloudn-test VNet")
                self.assertTrue(False)

            self.logger.info("%d licenses allocated before leaving cloudn-test VNet", lic_num2)

            self.logger.info("Waiting for leaving cloudn-test VNet ...")
            join_cloudn_vnet = JoinCloudNVPC(driver)
            self.assertTrue(join_cloudn_vnet.leave_cloudn_vpc(vnet_name))

            # check the number of licenses allocated after leaving cloudn-test VNet
            lic_view = ViewLicenses(driver)
            lic_num3 = lic_view.view_allocated_license()
            self.logger.info("%d licenses allocated after leaving cloudn-test VNet", lic_num3)
            if lic_num3 == lic_num1:
                self.logger.info("License allocated properly after leaving cloudn-test VNet")
                self.assertTrue(True)
            else:
                self.logger.error("License allocation is wrong after leaving cloudn-test VNet")
                self.assertTrue(False)
        except Exception as e:
            self.logger.exception("Join cloudn-test VNet Exception: " + str(e))
            self.assertTrue(False)
        finally:
            if inst_info:
                # Delete the user instance and related resource
                self.logger.info("Delete the user instance in VNet %s ...", vnet_name)
                cleanup_vnet_resources(self.logger, vnet_name, "West US", inst_info)

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()

if __name__ == "__main__":
    unittest.main()
