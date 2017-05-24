__author__ = 'lmxiang'

import unittest

from selenium import webdriver

from GUI import ConnectLegacyVPC
from GUI import ViewLicenses
from GUI import VpnAccessAddUsers
from GUI import VpnAccessDeleteUsers
from tests.utils.vpc_utils import *


class ConnectLegacyVPCTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Firefox()
        cls.driver.maximize_window()
        cls.logger = logging.getLogger("cloudn-test.tests.connect_legacy_vpc_tests")

    def test_connect_legacy_vpc(self):
        from tests.main import variables as _variables
        driver = self.driver
        _vpc_cidr = "10.20.0.0/16"
        _public_subnet = "10.20.1.0/24"
        _private_subnet = "10.20.v2/24"
        _vpn_subnet = "101.1.0.0/16"
        _instance_subnet = "10.20.1.0"
        _subnet_mask = "255.255.255.0"
        _local_cidr = _variables['local_cidr']
        _region = _variables['aws_region']
        _ami = _variables['aws_ami_id']
        _key = "latest1"
        vpc_info = {}
        instance_info = {}
        lic_num1 = 0

        self.logger.info("Connect to a legacy VPC with VPN access enabled ...")
        try:
            # check the number of license already allocated before connecting legacy VPC
            lic_view = ViewLicenses(driver, login_required=True)
            lic_num1 = lic_view.view_allocated_license()
            self.logger.info("%d licenses allocated before connecting legacy VPC", lic_num1)

            self.logger.info("Create a legacy VPC ...")
            vpc_info = create_legacy_vpc(self.logger, "vpc1", _vpc_cidr, _public_subnet, _private_subnet, region=_region)
            self.logger.info("Legacy VPC creation complete")

            connect_legacy_vpc = ConnectLegacyVPC(driver)

            self.logger.info("Start Connect Legacy VPC test")
            self.logger.info("Waiting for connecting legacy VPC ...")
            self.assertTrue(connect_legacy_vpc.fill_connect_legacy_vpc_form("aws",
                                                                            vpc_name="gateway1",
                                                                            vpc_id=vpc_info['vpc_id'],
                                                                            vpn_subnet=_vpn_subnet,
                                                                            public_subnet=_public_subnet,
                                                                            split_tunnel="Yes",
                                                                            additional_cidrs=_local_cidr,
                                                                            two_step_auth="Duo"))
            self.assertTrue(connect_legacy_vpc.click_connect_legacy_vpc_button("gateway1"))

            # add local CIDR to the gateway
            connect_legacy_vpc = ConnectLegacyVPC(driver)
            self.assertTrue(connect_legacy_vpc.allow_subnet("gateway1", _local_cidr))

            # check the number of licenses allocated after connecting legacy VPC
            lic_view = ViewLicenses(driver)
            lic_num2 = lic_view.view_allocated_license()
            self.logger.info("%d licenses allocated after connecting legacy VPC", lic_num2)
            if lic_num2 - lic_num1 == 1:
                self.logger.info("License allocated properly after connecting legacy VPC")
                self.assertTrue(True)
            else:
                self.logger.error("License allocation is wrong after connecting legacy VPC")
                self.assertTrue(False)

            self.logger.info("Create a user instance inside of vpc1 ...")
            instance_info = create_user_instance(driver, self.logger, "vpc1", _region, _ami, _key,
                                                 vpc_id=vpc_info['vpc_id'],
                                                 vpc_subnet_id=vpc_info['public_subnet_id'],
                                                 need_public_ip=False)
            self.logger.info("User instance creation complete")

            self.logger.info("Add a route in local instance to access legacy VPC subnet ...")
            modify_ip_route(self.logger, "add", _instance_subnet, _subnet_mask, _variables["cloudn_ip"], "eth0")

            self.logger.info("Pings from local instance to legacy VPC instance ...")
            self.assertTrue(vpn_ping_legacy_vpc(self.logger, vpc_info['vpc_id'], instance_info['instance_id']))

            vpn_user_add = VpnAccessAddUsers(driver)
            self.logger.info("Add one VPN user to the connected VPC ...")
            self.assertTrue(vpn_user_add.add_vpn_user("gateway1", "user11", _variables["cloudn_account_email"]))

            self.logger.info("Download OpenVPN configuration file from email attachment ...")
            file_path = download_openvpn_config(driver, self.logger,
                                                _variables["cloudn_account_email"],
                                                _variables["cloudn_email_pw"])

            self.logger.info("Upload the OpenVPN configuration file %s to OpenVPN client ...", file_path)
            file_name = os.path.basename(file_path)
            sftp_upload(self.logger, file_name)

            self.logger.info("Launch OpenVPN client and ping the user instance inside of the legacy VPC")
            self.assertTrue(openvpn_ping(driver, self.logger, file_name,
                                         "openvpn.auth.conf", "gateway1", instance_info['private_ip'], retries=3))

            self.logger.info("Download the OpenVPN log and ping results from OpenVPN client ...")
            time.sleep(5)
            sftp_download(self.logger)

            self.logger.info("Check OpenVPN log and ping results to verify the results ...")
            local_path = os.path.dirname(os.path.abspath(__file__)) + "\\..\\archives\\temp"
            openvpn_local = local_path + "\\openvpn.log"
            ping_local = local_path + "\\pingtest.log"

            self.assertTrue(check_openvpn_log(self.logger, openvpn_local))
            self.assertTrue(check_ping_log(self.logger, ping_local))

        except Exception as e:
            self.logger.exception("Connect Legacy VPC - OpenVPN Tests Exception: " + str(e))
            self.assertTrue(False)
        finally:
            try:
                vpn_user_delete = VpnAccessDeleteUsers(driver)
                self.logger.info("Delete the VPN user from connected VPC ...")
                self.assertTrue(vpn_user_delete.delete_vpn_user("gateway1", "user11"))

                lic_view = ViewLicenses(driver)
                lic_num3 = lic_view.view_allocated_license()
                self.logger.info("%d licenses allocated before disconnecting legacy VPC", lic_num3)

                self.logger.info("Waiting for disconnecting legacy VPC ...")
                disconnect_legacy_vpc = ConnectLegacyVPC(driver)
                self.assertTrue(disconnect_legacy_vpc.delete_subnet("gateway1"))
                self.assertTrue(disconnect_legacy_vpc.disconnect_legacy_vpc("gateway1"))

                # check the number of licenses allocated after leaving legacy VPC
                lic_view = ViewLicenses(driver)
                lic_num4 = lic_view.view_allocated_license()
                self.logger.info("%d licenses allocated after disconnecting legacy VPC", lic_num4)
                if lic_num3 - lic_num4 == 1 and lic_num4 == lic_num1:
                    self.logger.info("License allocated properly after disconnecting legacy VPC")
                    self.assertTrue(True)
                else:
                    self.logger.error("License allocation is wrong after disconnecting legacy VPC")
                    self.assertTrue(False)
            except Exception as e:
                self.logger.exception("Disconnect Legacy VPC Exception: " + str(e))
                self.assertTrue(False)
            finally:
                if instance_info:
                    delete_user_instance_by_id(self.logger, _region, instance_info['instance_id'])
                if vpc_info:
                    delete_legacy_vpc(self.logger, vpc_info)

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()

if __name__ == "__main__":
    unittest.main()