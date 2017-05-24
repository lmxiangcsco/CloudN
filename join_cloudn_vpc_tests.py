__author__ = 'lmxiang'

import unittest

from selenium import webdriver

from GUI import JoinCloudNVPC
from GUI import ViewLicenses
from tests.utils.vpc_utils import *


class JoinCloudNVPCTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Firefox()
        cls.driver.maximize_window()
        cls.logger = logging.getLogger("cloudn-test.tests.join_cloudn_vpc_tests")

    def test_join_cloudn_vpc(self):
        # Create on VPC called "vpc-regression" in US-West-1 from another cloudn-test controller which has a different public IP
        from tests.main import variables as _variables
        driver = self.driver
        cloud_type = "AWS"
        vpc_name = "vpc-cloudn"
        cidr_block = "10.100.8.0/24"
        instance_subnet = "10.100.8.0"
        instance_mask = "255.255.255.0"
        aws_key = "latest1"
        instance_info = {}

        try:
            # check the number of license already allocated before joining cloudn-test VPC
            lic_view = ViewLicenses(driver, login_required=True)
            lic_num1 = lic_view.view_allocated_license()
            self.logger.info("%d licenses allocated before joining cloudn-test VPC", lic_num1)

            join_cloudn_vpc = JoinCloudNVPC(driver)

            self.logger.info("Waiting for joining cloudn-test VPC ...")
            self.assertTrue(join_cloudn_vpc.join_cloudn_vpc(cloud_type, vpc_name, cidr_block, _variables['aws_region']))

            self.logger.info("Allow subnet for joined cloudn-test VPC ...")
            self.assertTrue(join_cloudn_vpc.allow_subnet(vpc_name))

            self.logger.info("Create a user instance in joined cloudn-test VPC ...")
            instance_info = create_user_instance(driver, self.logger, vpc_name,
                                                 _variables['aws_region'], _variables['aws_ami_id'], aws_key)

            self.logger.info("Add a route in local instance to access cloudn-test VPC subnets ...")
            modify_ip_route(self.logger, "add", instance_subnet, instance_mask, _variables["cloudn_ip"], "eth0")

            self.logger.info("Ping the user instance in joined cloudn-test VPC ...")
            self.assertTrue(vpn_ping_cloudn_vpc(driver, self.logger, vpc_name,
                                                _variables["cloudn_instance_ip"],
                                                _variables["cloudn_instance_username"],
                                                _variables["cloudn_instance_password"]))

            self.logger.info("Remove the route in local instance for accessing cloudn-test VPC subnets ...")
            modify_ip_route(self.logger, "del", instance_subnet, instance_mask, _variables["cloudn_ip"], "eth0")

            # check the number of licenses allocated after joining cloudn-test VPC
            lic_view = ViewLicenses(driver)
            lic_num2 = lic_view.view_allocated_license()
            self.logger.info("%d licenses allocated after joining legacy cloudn-test", lic_num2)
            if lic_num2 - lic_num1 == 1:
                self.logger.info("License allocated properly after joining cloudn-test VPC")
                self.assertTrue(True)
            else:
                self.logger.error("License allocation is wrong after joining cloudn-test VPC")
                self.assertTrue(False)

            self.logger.info("%d licenses allocated before leaving cloudn-test VPC", lic_num2)

            join_cloudn_vpc = JoinCloudNVPC(driver)

            self.logger.info("Delete subnet for joined cloudn-test VPC ...")
            self.assertTrue(join_cloudn_vpc.delete_subnet(vpc_name))

            self.logger.info("Waiting for leaving cloudn-test VPC ...")
            self.assertTrue(join_cloudn_vpc.leave_cloudn_vpc(vpc_name))

            # check the number of licenses allocated after leaving cloudn-test VPC
            lic_view = ViewLicenses(driver)
            lic_num3 = lic_view.view_allocated_license()
            self.logger.info("%d licenses allocated after leaving cloudn-test VPC", lic_num3)
            if lic_num3 == lic_num1:
                self.logger.info("License allocated properly after leaving cloudn-test VPC")
                self.assertTrue(True)
            else:
                self.logger.error("License allocation is wrong after leaving cloudn-test VPC")
                self.assertTrue(False)
        except Exception as e:
            self.logger.exception("Join cloudn-test VPC Exception: " + str(e))
            self.assertTrue(False)
        finally:
            if instance_info:
                # Delete the user instance
                delete_user_instance_by_id(self.logger, _variables['aws_region'], instance_info['instance_id'])
                # Delete the security group
                delete_security_group(self.logger, _variables['aws_region'], instance_info['sec_grp_id'])

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()

if __name__ == "__main__":
    unittest.main()