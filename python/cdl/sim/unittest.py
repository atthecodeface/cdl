class TestCase(unittest.TestCase):
    def do_memory_test(self, memory_type:cdl.sim.HardwareType, bits_per_enable:int, mif_filename:str, tv_filename:str)->None:
        hw = memory_type(bits_per_enable, os.path.join(module_root,mif_filename), os.path.join(module_root,tv_filename))
        hw.reset()
        hw.step(1000)
        hw.step(1000)
        self.assertTrue(hw.passed())

    # This is the first single-port test: 1024x16, rnw, no additional enables
    def test_1024x16_srw_rnw_no_enables(self)->None:
        self.do_memory_test(single_port_memory_srw_hw, 0, "single_port_memory_in.mif", "single_port_memory.tv")

    # This is the second single-port test: 1024x16, rnw, with write enable
    def test_1024x16_srw_rnw_write_enable(self)->None:
        self.do_memory_test(single_port_memory_srw_hw, 16, "single_port_memory_in.mif", "single_port_memory_1_be.tv")

    # This is the third single-port test: 1024x16, rnw, with individaul byte write enables
    def test_1024x16_srw_rnw_byte_write_enable(self)->None:
        self.do_memory_test(single_port_memory_srw_hw, 8, "single_port_memory_in.mif", "single_port_memory_2_be.tv")

    # This is the first  single multi-port test: 1024x16, rnw, no additional enables
    def test_1024x16_srnw_byte_write_enable(self)->None:
        self.do_memory_test(single_port_memory_hw, 0, "single_port_memory_in.mif", "single_port_memory.tv")

    # This is the second single multi-port test: 1024x16, rnw, with write enable
    def test_1024x16_srnw_write_enable(self)->None:
        self.do_memory_test(single_port_memory_hw, 16, "single_port_memory_in.mif", "single_port_memory_1_be.tv")

    # This is the third single multi-port test: 1024x16, rnw, with individaul byte write enables
    def test_1024x16_srnw_byte_write_enable2(self)->None:
        self.do_memory_test(single_port_memory_hw, 8, "single_port_memory_in.mif", "single_port_memory_2_be.tv")

    # This is the first  dual-port test: 1024x16, rnw, no additional enables
    def test_1024x16_drnw_byte_write_enable(self)->None:
        self.do_memory_test(dual_port_memory_hw, 0, "dual_port_memory_in.mif", "dual_port_memory.tv")

    # This is the second dual-port test: 1024x16, rnw, with write enable
    def test_1024x16_drnw_write_enable(self)->None:
        self.do_memory_test(dual_port_memory_hw, 16, "dual_port_memory_in.mif", "dual_port_memory_1_be.tv")

    # This is the third dual-port test: 1024x16, rnw, with individaul byte write enables
    def test_1024x16_drnw_byte_write_enable2(self)->None:
        self.do_memory_test(dual_port_memory_hw, 8, "dual_port_memory_in.mif", "dual_port_memory_2_be.tv")


if __name__ == '__main__':
    unittest.main()
