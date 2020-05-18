#a Imports
from threading import Lock
from cdl.sim import ThExecFile, LogEventParser
from cdl.sim import HardwareThDut, OptionsDict
from cdl.sim import TestCase

from typing import Optional

#c log_test_harness_exec_file
class log_test_harness_exec_file(ThExecFile):
    th_name = "log_toggle test harness"
    def exec_init(self) -> None:
        self.toggle_log_event  = self.log_event("toggle", "n", "arg")
        self.log_fifo          = self.sim_fifo(1024)
        self.die_event         = self.sim_event()
        self.log_events_unhandled = 0
        self.state_lock = Lock()
        ThExecFile.exec_init(self)
        pass

    def do_while_locked(self, fn):
        self.state_lock.acquire()
        fn()
        self.state_lock.release()
        pass

    def locked_mla_value(self, n, m, a):
        self.state_lock.acquire()
        setattr(self, n, getattr(self, n) * m + a)
        self.state_lock.release()
        pass

    def waiter(self):
        self.die_event.wait()
        print("Waiter done waiting")
        pass

    def log_toggle_tracker(self, max_events):
        last_cycle = None
        inter_despatch_delay = 0
        n = 0
        self.log_th            = self.log_recorder("th") # We want individual loggers
        while max_events>0:
            if self.die_event.fired(): break
            self.bfm_wait(100)
            while self.log_th.num_events()>0:
                event = self.log_th.event_pop().split(",")
                global_cycle = int(event[2])
                if last_cycle is not None:
                    if inter_despatch_delay!=0:
                        self.compare_expected("delay between toggles constant", global_cycle-last_cycle, inter_despatch_delay)
                        pass
                    inter_despatch_delay = global_cycle - last_cycle
                    pass
                last_cycle = global_cycle
                num_remaining = int(event[5],16)
                self.compare_expected("log event argument",num_remaining,max_events)
                # self.verbose.info("Message %s"%str(event))
                self.locked_mla_value("log_events_unhandled",1,-1)
                max_events = max_events-1
                if max_events==0: break
                break
            pass
        self.passtest("log_toggle_tracker done")
        pass

    margin_32 = 0.05
    margin_256= 0.15
    def log_dut_tracker(self):
        class DutLogParser(LogEventParser):
            def filter_module(self, module_name:str) -> bool : return module_name=="dut"
            def map_log_type(self, log_type:str) -> Optional[str] :
                if log_type in self.attr_map: return log_type
                return None
            attr_map = {"has11111":{"lfsr":0}, "has01010101":{"3210":0, "7654":1}}
            pass
        self.log_dut           = self.log_recorder("dut")
        self.log_dut_parser    = DutLogParser()
        number_one_in_32 = 0
        number_one_in_256 = 0
        first_cycle = 0
        while not self.die_event.fired():
            while self.log_dut.num_events()>0:
                l = self.log_dut_parser.parse_log_event(self.log_dut.event_pop())
                if l is None: continue
                if l.log_type == "has11111":    number_one_in_32 = number_one_in_32 +1
                if l.log_type == "has01010101": number_one_in_256 = number_one_in_256 +1
                if first_cycle==0: first_cycle=l.global_cycle
                last_cycle = l.global_cycle
                pass
            self.bfm_wait(100)
            pass
        total_cycles = (last_cycle-first_cycle) // self.ticks_per_cycle()
        expected_per_32  = total_cycles/32
        expected_per_256 = total_cycles/256
        if number_one_in_32 / expected_per_32 < 1.0 - self.margin_32:
            self.failtest("Too few one-in-32's from LFSR (ratio was %f)"%(number_one_in_32/expected_per_32))
            pass
        if number_one_in_32 / expected_per_32 > 1.0 + self.margin_32:
            self.failtest("Too many one-in-32's from LFSR (ratio was %f)"%(number_one_in_32/expected_per_32))
            pass
        if number_one_in_256 / expected_per_256 < 1.0 - self.margin_256:
            self.failtest("Too few one-in-256's from LFSR (ratio was %f)"%(number_one_in_256/expected_per_256))
            pass
        if number_one_in_256 / expected_per_256 > 1.0 + self.margin_256:
            self.failtest("Too many one-in-256's from LFSR (ratio was %f)"%(number_one_in_256/expected_per_256))
            pass
        self.passtest("log_dut_tracker done")
        pass

    def run(self) -> None:
        # Logger recorders go in run as they need to have the events they are logging already defined
        self.bfm_wait(1)
        self.locked_mla_value("log_events_unhandled",0,0)
        self.bfm_wait(10)
        self.die_event.reset()
        self.spawn(self.log_toggle_tracker,10)
        self.spawn(self.log_dut_tracker)
        self.spawn(self.waiter)

        self.bfm_wait(10)
        for i in range(10):
            self.toggle_log_event.occurred(i,10-i)
            self.locked_mla_value("log_events_unhandled",1,1)
            self.bfm_wait(10)
            pass

        self.bfm_wait_until_test_done(100)
        self.die_event.fire()
        self.bfm_wait(10)
        self.compare_expected("all th toggle events handled",self.log_events_unhandled,0)
        self.passtest("Test succeeded")
        pass

#c DutHardware
class DutHardware(HardwareThDut):
    clock_desc = [("io_clock",(0,1,1)),
    ]
    module_name = "lfsr_log_tracker"
    dut_inputs = {
    }
    dut_outputs = {"toggle":1,
    }
    th_options = {"signal_object_prefix":"signal__",
                 }
    reset_desc = {"name":"io_reset", "init_value":1, "wait":9}
    th_exec_file_object_fn = log_test_harness_exec_file
    loggers = { "a": {"modules":"dut", "verbose":0}
                }
    pass

#c TestVector
class TestVector(TestCase):
    hw = DutHardware
    def test_log_1(self)->None:
        self.run_test(hw_args={"verbosity":0}, run_time=250000)
        pass
    pass
