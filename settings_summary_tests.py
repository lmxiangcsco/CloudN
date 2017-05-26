__author__ = 'reyhong'

import logging
import unittest

from GUI.Settings.Summary.setting_summary import SettingSummary
from selenium import webdriver


class SettingDeviceSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Firefox()
        cls.driver.maximize_window()
        cls.logger = logging.getLogger("cloudn-test.tests.Settings.settings_summary_tests")

    def test_setting_system_upgrade(self):
        from tests.main import variables
        driver = self.driver

        # Create instance
        sys_summary = SettingSummary(driver)

        # Check all field
        self.assertTrue(sys_summary.check_customerid(variables["customer_id"]))
        self.assertTrue(sys_summary.check_max_vpc_num(variables["vpc_num"]))
        self.assertTrue(sys_summary.check_interface_ip(variables["cloudn_ip"]))
        self.assertTrue(sys_summary.check_interface_mask(variables["cloudn_ip_mask"]))
        self.assertTrue(sys_summary.check_default_gateway(variables["cloudn_ip"]))
        self.assertTrue(sys_summary.check_primary_dns(variables["cloudn_dns1"]))
        self.assertTrue(sys_summary.check_secondary_dns(variables["cloudn_dns2"]))
        self.assertTrue(sys_summary.check_account_name(variables["cloudn_account_name"]))
        self.assertTrue(sys_summary.check_aws_account_num(variables["aws_account_number"]))
        self.assertTrue(sys_summary.check_aws_keyID(variables["aws_access_keyid"]))
        self.assertTrue(sys_summary.check_account_email(variables["cloudn_account_email"]))

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()

if __name__ == "__main__":
    unittest.main()