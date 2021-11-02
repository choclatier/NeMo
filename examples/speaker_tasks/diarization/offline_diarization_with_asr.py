# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import omegaconf
from omegaconf import OmegaConf

from nemo.collections.asr.parts.utils.diarization_utils import ASR_DIAR_OFFLINE
from nemo.collections.asr.parts.utils.speaker_utils import audio_rttm_map
from nemo.core.config import hydra_runner
from nemo.utils import logging


"""
Currently Supported ASR models:

QuartzNet15x5Base-En
stt_en_conformer_ctc_large
"""


@hydra_runner(config_path="conf", config_name="offline_diarization_with_asr.yaml")
def main(cfg):

    logging.info(f'Hydra config: {OmegaConf.to_yaml(cfg)}')

    asr_diar_offline = ASR_DIAR_OFFLINE(**cfg.diarizer.asr.parameters)
    asr_diar_offline.root_path = cfg.diarizer.out_dir

    AUDIO_RTTM_MAP = audio_rttm_map(cfg.diarizer.manifest_filepath)
    asr_diar_offline.AUDIO_RTTM_MAP = AUDIO_RTTM_MAP
    asr_model = asr_diar_offline.set_asr_model(cfg.diarizer.asr.parameters['model_path'])

    word_list, word_ts_list = asr_diar_offline.run_ASR(asr_model)

    diar_labels = asr_diar_offline.run_diarization(cfg, word_ts_list,)

    ref_rttm_file_list = [value['rttm_filepath'] for key, value in AUDIO_RTTM_MAP.items()]

    if len(ref_rttm_file_list) and ref_rttm_file_list[0] is not None:

        ref_labels_list, DER_result_dict = asr_diar_offline.eval_diarization(AUDIO_RTTM_MAP=AUDIO_RTTM_MAP)

        total_riva_dict = asr_diar_offline.write_json_and_transcript(word_list, word_ts_list)

        WDER_dict = asr_diar_offline.get_WDER(total_riva_dict, DER_result_dict, ref_labels_list)
        effective_wder = asr_diar_offline.get_effective_WDER(DER_result_dict, WDER_dict)

        logging.info(
            f"\nDER  : {DER_result_dict['total']['DER']:.4f} \
            \nFA   : {DER_result_dict['total']['FA']:.4f} \
            \nMISS : {DER_result_dict['total']['MISS']:.4f} \
            \nCER  : {DER_result_dict['total']['CER']:.4f} \
            \nWDER : {WDER_dict['total']:.4f} \
            \neffective WDER : {effective_wder:.4f} \
            \nspk_counting_acc : {DER_result_dict['total']['spk_counting_acc']:.4f}"
        )

    else:
        total_riva_dict = asr_diar_offline.write_json_and_transcript(diar_labels, word_list, word_ts_list)


if __name__ == '__main__':
    main()
