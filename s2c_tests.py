__author__ = 'lmxiang'

"""
Prerequisites:
- Create two VPCs called VPC1 and VPC2. VPC1 is the cloud side and VPC2 simulates on-prem
- Launch two gateways in VPC1. GW1_PRI is the primary gateway for HA and GW1_BKP is the backup gateway for HA
- Launch one gateway in VPC2.
- Launch one ubuntu instance in VPC1 as the source of ping traffic
- Launch one ubuntu instance in VPC2 as the destination of ping traffic
- Specify a folder at test machine for site2cloud configuration template download

Test Procedures:
- Create one site2cloud connection at GW1
- Download the configuration template with 'Aviatrix' as vendor from GW1
- Create one site2cloud connection at GW2 by importing the configuration template downloaded from GW1
- Send pings from ubuntu VM in VPC1 to ubuntu VM in VPC2 and check the ping success rate
- Check tunnel status at both GW1 and GW2
- Delete the site2cloud connections at both GW1 and GW2

Site2cloud Connection Types:
- unmapped, without HA
- mapped, without HA
- ummapped with HA
- mapped with HA
- unmapped and null encryption
"""

import unittest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from GUI.v2.lib.common_elements import *
from tests.utils.test_utils import avx_logger, find_files_in_directory, delete_files_in_directory
from tests.utils.vpc_utils import ssh_from_instance, ping_from_instance

import GUI.v2.site2cloud.s2c_conn as pages
import os

class S2C_Tests(unittest.TestCase):
    """
    Site2Cloud end-to-end solution tests
    """

    @classmethod
    def setUpClass(cls):
        cls.logger =avx_logger()
        chrome_options = Options()
        # folder used for Chrome to download files
        cls.dir_path = "C:\\Users\\lmxiang\\ChromeDownload"
        prefs = {"download.default_directory": cls.dir_path}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--disable-extensions")
        cls.driver = webdriver.Chrome(chrome_options=chrome_options)
        cls.driver.maximize_window()

    def test_s2c(self):
        self.logger.info("Start Adding Site2Cloud Connection on Gateway1")

        cloud_region = "us-east-1"
        VPC1_VM_ID = "i-4b243b5c"
        VPC1_VM_PUB_IP = "54.173.243.176"
        VPC2_VM_PRV_IP = "10.0.0.126"
        VPC2_VM_VIRT_PRV_IP = "10.2.0.126"
        ssh_key_file = r'..\etc\keys\AWSKeys\useast.pem'
        host_key_file = r'..\etc\known_hosts'
        download_dir = "C:\\Users\\lmxiang\\ChromeDownload"
        ssh_key = os.path.join(os.path.dirname(os.path.realpath(__file__)), ssh_key_file)
        host_key = os.path.join(os.path.dirname(os.path.realpath(__file__)), host_key_file)

        GW1_NAME_PRI = "ProdVPC-gw123"
        GW1_NAME_BKP = "ProdVPC-gw456"
        GW2_public_ip = "52.206.236.82"
        VPC1_CIDR_REAL = "172.19.0.0/16"
        VPC1_CIDR_VIRT = "10.1.0.0/16"
        VPC2_CIDR_REAL = "10.0.0.0/16"
        VPC2_CIDR_VIRT = "10.2.0.0/16"
        VPC1_ID = "vpc-01992565"
        VPC2_ID = "vpc-bfba09db"
        GW1_s2c_conn_name = "ProdConn"
        GW2_s2c_conn_name = "StagingConn"
        config_file_name = VPC1_ID + "-" + GW1_s2c_conn_name + ".txt"
        tunnel_status_check_retries = 10
        GW1_tunnel_up = False
        GW2_tunnel_up = False

        unmapped_basic = {"description": "Basic unmapped site2cloud connection",
                          "HA": "disable",
                          "vpc_id": VPC1_ID,
                          "conn_type": "Unmapped",
                          "primary_gw": GW1_NAME_PRI,
                          "conn_name": GW1_s2c_conn_name,
                          "customer_gw_ip": GW2_public_ip,
                          "customer_nw_real":VPC2_CIDR_REAL
                          }

        mapped_basic = {"description": "Mapped site2cloud connection",
                        "HA": "disable",
                        "vpc_id": VPC1_ID,
                        "conn_type": "Mapped",
                        "primary_gw": GW1_NAME_PRI,
                        "conn_name": GW1_s2c_conn_name,
                        "customer_gw_ip": GW2_public_ip,
                        "customer_nw_real": VPC2_CIDR_REAL,
                        "customer_nw_virtual": VPC2_CIDR_VIRT,
                        "cloud_sub_real": VPC1_CIDR_REAL,
                        "cloud_sub_virtual": VPC1_CIDR_VIRT
                        }

        unmapped_ha = {"description": "Site2cloud unmapped HA",
                       "HA": "enable",
                       "vpc_id": VPC1_ID,
                       "conn_type": "Unmapped",
                       "primary_gw": GW1_NAME_PRI,
                       "backup_gw": GW1_NAME_BKP,
                       "conn_name": GW1_s2c_conn_name,
                       "customer_gw_ip": GW2_public_ip,
                       "customer_nw_real": VPC2_CIDR_REAL,
                       "cloud_sub_real": VPC1_CIDR_REAL,
                       "null_encr": "deselect"
                       }

        mapped_ha = {"description": "Site2cloud mapped HA",
                     "HA": "enable",
                     "vpc_id": VPC1_ID,
                     "conn_type": "Mapped",
                     "primary_gw": GW1_NAME_PRI,
                     "backup_gw": GW1_NAME_BKP,
                     "conn_name": GW1_s2c_conn_name,
                     "customer_gw_ip": GW2_public_ip,
                     "customer_nw_real": VPC2_CIDR_REAL,
                     "customer_nw_virtual": VPC2_CIDR_VIRT,
                     "cloud_sub_real": VPC1_CIDR_REAL,
                     "cloud_sub_virtual": VPC1_CIDR_VIRT,
                     "null_encr": "deselect"
                     }

        unmapped_null = {"description": "Null encryption",
                        "HA": "disable",
                        "vpc_id": VPC1_ID,
                        "conn_type": "Unmapped",
                        "primary_gw": GW1_NAME_PRI,
                        "conn_name": GW1_s2c_conn_name,
                        "customer_gw_ip": GW2_public_ip,
                        "customer_nw_real": VPC2_CIDR_REAL,
                        "cloud_sub_real": VPC1_CIDR_REAL,
                        "null_encr": "select"
                        }

        #s2c_conn_list = [unmapped_basic, mapped_basic, unmapped_ha, mapped_ha, unmapped_null]
        s2c_conn_list = [unmapped_null]

        config = {"vendor": "Aviatrix",
                  "platform": "UCC",
                  "software": "1.0"
                  }

        s2c_new_gw1 = pages.S2C_New(self.driver, login_required=True)
        self.logger.info("Navigating to Site2Cloud")
        s2c_new_gw1.navigate_to_s2c()
        time.sleep(5)

        self.logger.info("Check if Site2Cloud is present in the current view area...")
        assert s2c_new_gw1.match_view_title(),"Site2Cloud view is not present"

        for s2c_conn in s2c_conn_list:
            # Remove all files in download directory
            delete_files_in_directory(download_dir)

            self.logger.info("Click 'Add New' button to create a new site2cloud connection...")
            s2c_new_gw1.new_button = "new"
            time.sleep(5)

            assert s2c_new_gw1.fill_conn_fields(**s2c_conn),"Fail to fill in Site2Cloud connection fields"
            s2c_new_gw1.ok_button = "ok"
            time.sleep(10)
            toaster_result = s2c_new_gw1.s2c_toaster.lower()
            assert ("success" in toaster_result),"Fail to create Site2Cloud connection: "+toaster_result
            time.sleep(5)

            self.logger.info("Download configuration template...")
            s2c_view = pages.S2C_View(self.driver, login_required=False)
            try:
                # Find the site2cloud connection and click on it
                s2c_view.find_s2c_conn(GW1_s2c_conn_name)
                time.sleep(5)

                # Start to download its configuration template
                for keys,values in config.items():
                    self.logger.info("%s : %s" % (keys, values))
                s2c_view.download_config(config["vendor"], config["platform"], config["software"])
                time.sleep(20)
            except (TimeoutException, NoSuchElementException) as e:
                self.logger.debug("Can not find the table with exception %s", str(e))
                assert False

            # Search download folder to find the config file
            config_file = find_files_in_directory(self.dir_path, config_file_name)
            if not config_file:
                self.logger.error("Can't find the downloaded configuration file %s", config_file_name)
                assert False
            else:
                config_file_abs = os.path.join(download_dir, config_file_name)
                self.logger.info("Downloaded configuration file is %s", config_file_abs)

            self.logger.info("Start Importing Site2Cloud Connection")

            s2c_new_gw2 = pages.S2C_New(self.driver, login_required=False)

            self.logger.info("Click 'Add New' button to create a new site2cloud connection...")
            s2c_new_gw2.new_button = "new"
            time.sleep(5)

            elm = self.driver.find_element_by_xpath("//input[@type='file']")
            elm.send_keys(config_file_abs)
            time.sleep(5)

            s2c_new_gw2.select_vpc_id = VPC2_ID
            self.logger.debug("Site2Cloud VPC ID/VNet Name: %s", VPC2_ID)

            s2c_new_gw2.input_conn_name = GW2_s2c_conn_name
            self.logger.debug("Site2Cloud Connection Name: %s", GW2_s2c_conn_name)
            time.sleep(5)

            s2c_new_gw2.ok_button = "ok"
            time.sleep(5)
            toaster_result = s2c_new_gw2.s2c_toaster.lower()
            assert ("successfully" in toaster_result), "Fail to create Site2Cloud connection: " + toaster_result
            time.sleep(5)

            self.logger.info("SSH into the VM in VPC1")
            ssh_client = ssh_from_instance(self.logger, cloud_region, VPC1_VM_ID,
                                           VPC1_VM_PUB_IP, ssh_key, host_key, "ubuntu")

            self.logger.info("Ping the target IP %s", VPC2_VM_PRV_IP)
            if s2c_conn['conn_type'].lower() == "unmapped":
                self.assertTrue(ping_from_instance(self.logger, ssh_client, VPC2_VM_PRV_IP, retries=5))
            if s2c_conn['conn_type'].lower() == "mapped":
                self.assertTrue(ping_from_instance(self.logger, ssh_client, VPC2_VM_VIRT_PRV_IP, retries=5))

            s2c_status = pages.S2C_View(self.driver, login_required=False)
            self.logger.info("Check site2cloud %s tunnel status" % GW1_s2c_conn_name)
            for retry in range(0, tunnel_status_check_retries):
                self.driver.refresh()
                time.sleep(10)
                GW1_status = s2c_status.get_s2c_element(GW1_s2c_conn_name, "Status")
                self.logger.info("site2cloud tunnel status: " + GW1_status)
                if "up" in GW1_status.lower():
                    GW1_tunnel_up = True
                    break
                else:
                    self.logger.info("site2cloud tunnel current status: %s", GW1_status)
                    time.sleep(5)
            if GW1_tunnel_up:
                self.logger.info("site2cloud %s tunnel is up", GW1_s2c_conn_name)
                assert True
            else:
                self.logger.error("site2cloud %s tunnel not up", GW1_s2c_conn_name)
                assert False

            self.logger.info("Check site2cloud %s tunnel status" % GW2_s2c_conn_name)
            for retry in range(0, tunnel_status_check_retries):
                self.driver.refresh()
                time.sleep(10)
                GW2_status = s2c_status.get_s2c_element(GW2_s2c_conn_name, "Status")
                self.logger.info("site2cloud tunnel status: " + GW2_status)
                if "up" in GW2_status.lower():
                    GW2_tunnel_up = True
                    break
                else:
                    time.sleep(5)
            if GW2_tunnel_up:
                self.logger.info("site2cloud %s tunnel is up", GW2_s2c_conn_name)
                assert True
            else:
                self.logger.error("site2cloud %s tunnel not up", GW2_s2c_conn_name)
                assert False

            s2c_conn_names = [GW1_s2c_conn_name, GW2_s2c_conn_name]

            try:
                table = self.driver.find_element_by_css_selector("table.aws-accounts-table")

                td_index = s2c_status.find_delete_col(table)

                for s2c_conn_name in s2c_conn_names:
                    tr_index = s2c_status.find_delete_row(table, s2c_conn_name)
                    self.logger.debug("Click 'Delete' button for Site2Cloud %s", s2c_conn_name)
                    xpath = "//table/tbody/tr[" + str(tr_index) + "]/td[" + str(td_index) + "]/button"
                    table.find_element_by_xpath(xpath).click()
                    time.sleep(2)
                    handle_alert(self)
                    time.sleep(2)
                    toaster_result = s2c_status.s2c_toaster.lower()
                    assert ("success" in toaster_result), "Fail to delete " + s2c_conn_name
            except (TimeoutException, NoSuchElementException) as e:
                self.logger.debug("Can not find the table with exception %s", str(e))
                return False

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()

if __name__ == "__main__":
    unittest.main()