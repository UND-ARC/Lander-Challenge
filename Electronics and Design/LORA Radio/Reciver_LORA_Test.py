#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Reciver_LORA_Test
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
import pmt
from gnuradio import blocks, gr
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import iio
import gnuradio.lora_sdr as lora_sdr
import sip
import threading


def snipfcn_snippet_0(self):
    import sys; sys.path.append('/usr/lib/python3.13/site-packages')


class Reciver_LORA_Test(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Reciver_LORA_Test", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Reciver_LORA_Test")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "Reciver_LORA_Test")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.sample_rate = sample_rate = 1000000
        self.btn_trigger_start = btn_trigger_start = 0
        self.btn_trigger_ESTOP = btn_trigger_ESTOP = 0
        self.Spreading_Factor = Spreading_Factor = 7
        self.Frequency = Frequency = 915300000

        ##################################################
        # Blocks
        ##################################################

        self._btn_trigger_start_choices = {'Pressed': 1, 'Released': 0}

        _btn_trigger_start_toggle_button = qtgui.ToggleButton(self.set_btn_trigger_start, 'START', self._btn_trigger_start_choices, False, 'value')
        _btn_trigger_start_toggle_button.setColors("default", "default", "default", "default")
        self.btn_trigger_start = _btn_trigger_start_toggle_button

        self.top_layout.addWidget(_btn_trigger_start_toggle_button)
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            Frequency, #fc
            1000000, #bw
            "", #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0.enable_grid(False)
        self.qtgui_freq_sink_x_0.set_fft_average(0.2)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_0_win)
        self.lora_tx_0 = lora_sdr.lora_sdr_lora_tx(
            bw=125000,
            cr=1,
            has_crc=True,
            impl_head=False,
            samp_rate=sample_rate,
            sf=Spreading_Factor,
         ldro_mode=0,frame_zero_padd=1280,sync_word=[0x12] )
        self.lora_rx_0 = lora_sdr.lora_sdr_lora_rx( bw=125000, cr=1, has_crc=True, impl_head=False, pay_len=255, samp_rate=sample_rate, sf=Spreading_Factor, sync_word=[0x12], soft_decoding=True, ldro_mode=2, print_rx=[False,True])
        self.iio_pluto_source_0 = iio.fmcomms2_source_fc32('ip:192.168.2.1' if 'ip:192.168.2.1' else iio.get_pluto_uri(), [True, True], 32768)
        self.iio_pluto_source_0.set_len_tag_key('packet_len')
        self.iio_pluto_source_0.set_frequency(Frequency)
        self.iio_pluto_source_0.set_samplerate(sample_rate)
        self.iio_pluto_source_0.set_gain_mode(0, 'slow_attack')
        self.iio_pluto_source_0.set_gain(0, 15)
        self.iio_pluto_source_0.set_quadrature(True)
        self.iio_pluto_source_0.set_rfdc(True)
        self.iio_pluto_source_0.set_bbdc(True)
        self.iio_pluto_source_0.set_filter_params('Auto', '', 0, 0)
        self.iio_pluto_sink_0 = iio.fmcomms2_sink_fc32('ip:192.168.2.1' if 'ip:192.168.2.1' else iio.get_pluto_uri(), [True, True], 32768, False)
        self.iio_pluto_sink_0.set_len_tag_key('')
        self.iio_pluto_sink_0.set_bandwidth(20000000)
        self.iio_pluto_sink_0.set_frequency(Frequency)
        self.iio_pluto_sink_0.set_samplerate(sample_rate)
        self.iio_pluto_sink_0.set_attenuation(0, 20)
        self.iio_pluto_sink_0.set_filter_params('Auto', '', 0, 0)
        _btn_trigger_ESTOP_push_button = Qt.QPushButton('ESTOP')
        _btn_trigger_ESTOP_push_button = Qt.QPushButton('ESTOP')
        self._btn_trigger_ESTOP_choices = {'Pressed': 1, 'Released': 0}
        _btn_trigger_ESTOP_push_button.pressed.connect(lambda: self.set_btn_trigger_ESTOP(self._btn_trigger_ESTOP_choices['Pressed']))
        _btn_trigger_ESTOP_push_button.released.connect(lambda: self.set_btn_trigger_ESTOP(self._btn_trigger_ESTOP_choices['Released']))
        self.top_layout.addWidget(_btn_trigger_ESTOP_push_button)
        self.blocks_mute_xx_0 = blocks.mute_cc(bool(not btn_trigger_start))
        self.blocks_message_strobe_0_0 = blocks.message_strobe(pmt.intern("ESTOP"), 1000)
        self.blocks_message_strobe_0 = blocks.message_strobe(pmt.intern("                     STARTMAIN"), 500)
        self.blocks_message_debug_0 = blocks.message_debug(True, gr.log_levels.info)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_message_strobe_0, 'strobe'), (self.lora_tx_0, 'in'))
        self.msg_connect((self.lora_rx_0, 'out'), (self.blocks_message_debug_0, 'print'))
        self.msg_connect((self.lora_rx_0, 'out'), (self.blocks_message_debug_0, 'log'))
        self.connect((self.blocks_mute_xx_0, 0), (self.iio_pluto_sink_0, 0))
        self.connect((self.iio_pluto_source_0, 0), (self.lora_rx_0, 0))
        self.connect((self.iio_pluto_source_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.lora_tx_0, 0), (self.blocks_mute_xx_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "Reciver_LORA_Test")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_sample_rate(self):
        return self.sample_rate

    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate
        self.iio_pluto_sink_0.set_samplerate(self.sample_rate)
        self.iio_pluto_source_0.set_samplerate(self.sample_rate)

    def get_btn_trigger_start(self):
        return self.btn_trigger_start

    def set_btn_trigger_start(self, btn_trigger_start):
        self.btn_trigger_start = btn_trigger_start
        self.blocks_mute_xx_0.set_mute(bool(not self.btn_trigger_start))

    def get_btn_trigger_ESTOP(self):
        return self.btn_trigger_ESTOP

    def set_btn_trigger_ESTOP(self, btn_trigger_ESTOP):
        self.btn_trigger_ESTOP = btn_trigger_ESTOP

    def get_Spreading_Factor(self):
        return self.Spreading_Factor

    def set_Spreading_Factor(self, Spreading_Factor):
        self.Spreading_Factor = Spreading_Factor
        self.lora_tx_0.set_sf(self.Spreading_Factor)

    def get_Frequency(self):
        return self.Frequency

    def set_Frequency(self, Frequency):
        self.Frequency = Frequency
        self.iio_pluto_sink_0.set_frequency(self.Frequency)
        self.iio_pluto_source_0.set_frequency(self.Frequency)
        self.qtgui_freq_sink_x_0.set_frequency_range(self.Frequency, 1000000)




def main(top_block_cls=Reciver_LORA_Test, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
