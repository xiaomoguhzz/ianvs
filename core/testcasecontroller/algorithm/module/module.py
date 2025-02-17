# Copyright 2022 The KubeEdge Authors.
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

""" Algorithm Module"""

import copy

from sedna.common.class_factory import ClassFactory, ClassType

from core.common import utils
from core.common.constant import ModuleType
from core.testcasecontroller.generation_assistant import get_full_combinations


class Module:
    """
    Algorithm Module:
    provide the configuration and the calling functions of the algorithm module.
    Notes:
          1. Ianvs serves as testing tools for test objects, e.g., algorithms.
          2. Ianvs does NOT include code directly on test object.
          3. Algorithms serve as typical test objects in Ianvs
          and detailed algorithms are thus NOT included in this Ianvs python file.
          4. As for the details of example test objects, e.g., algorithms,
          please refer to third party packages in Ianvs example.
          For example, AI workflow and interface pls refer to sedna
          (sedna docs: https://sedna.readthedocs.io/en/latest/api/lib/index.html),
          and module implementation pls refer to `examples' test algorithms`,
          e.g., basemodel.py, hard_example_mining.py.

    Parameters
    ----------
    config : dict
         config of the algorithm module, includes: type, name,
         url of the python file that defines algorithm module,
         hyperparameters of the calling functions of algorithm module, etc.

    """

    def __init__(self, config):
        self.type: str = ""
        self.name: str = ""
        self.url: str = ""
        self.hyperparameters = None
        self.hyperparameters_list = None
        self._parse_config(config)

    def _check_fields(self):
        if not self.type and not isinstance(self.type, str):
            raise ValueError(f"module type({self.type}) must be provided and be string type.")

        types = [e.value for e in ModuleType.__members__.values()]
        if self.type not in types:
            raise ValueError(f"not support module type({self.type}."
                             f"the following paradigms can be selected: {types}")

        if not self.name and not isinstance(self.name, str):
            raise ValueError(f"module name({self.name}) must be provided and be string type.")

        if not isinstance(self.url, str):
            raise ValueError(f"module url({self.url}) must be string type.")

    def basemodel_func(self):
        """
        get basemodel module function of the module.

        Returns
        --------
        function

        """

        if not self.url:
            raise ValueError(f"url({self.url}) of basemodel module must be provided.")

        try:
            utils.load_module(self.url)
            # pylint: disable=E1134
            basemodel = ClassFactory.get_cls(type_name=ClassType.GENERAL,
                                             t_cls_name=self.name)(**self.hyperparameters)
        except Exception as err:
            raise RuntimeError(f"basemodel module loads class(name={self.name}) failed, "
                            f"error: {err}.") from err

        return basemodel

    def hard_example_mining_func(self):
        """
        get hard example mining function of the module.

        Returns:
        --------
        function

        """

        if self.url:
            try:
                utils.load_module(self.url)
                # pylint: disable=E1134
                func = ClassFactory.get_cls(
                    type_name=ClassType.HEM, t_cls_name=self.name)(**self.hyperparameters)

                return func
            except Exception as err:
                raise RuntimeError(f"hard_example_mining module loads class"
                                f"(name={self.name}) failed, error: {err}.") from err

        # call built-in hard example mining function
        hard_example_mining = {"method": self.name}
        if self.hyperparameters:
            hard_example_mining["param"] = self.hyperparameters

        return hard_example_mining

    def get_module_func(self, module_type):
        """
        get function of algorithm module by using module type

        Parameters
        ---------
        module_type: string
            module type, e.g.: basemodel, hard_example_mining, etc.

        Returns
        ------
        function

        """
        func_name = f"{module_type}_func"
        return getattr(self, func_name)

    def _parse_config(self, config):
        # pylint: disable=C0103
        for k, v in config.items():
            if k == "hyperparameters":
                self.hyperparameters_list = self._parse_hyperparameters(v)
            if k in self.__dict__:
                self.__dict__[k] = v

        self._check_fields()

    def _parse_hyperparameters(self, config):
        # hp is short for hyperparameters
        base_hps = {}
        hp_name_values_list = []
        for ele in config:
            hp_config = ele.popitem()
            hp_name = hp_config[0]
            hp_values = hp_config[1].get("values")
            if hp_name == "other_hyperparameters":
                base_hps = self._parse_other_hyperparameters(hp_values)
            else:
                hp_name_values_list.append((hp_name, hp_values))

        hp_combinations_list = get_full_combinations(hp_name_values_list)

        hps_list = []
        for hp_combinations in hp_combinations_list:
            base_hps_copy = copy.deepcopy(base_hps)
            base_hps_copy.update(**hp_combinations)
            hps_list.append(base_hps_copy)

        return hps_list

    @classmethod
    def _parse_other_hyperparameters(cls, config_files):
        base_hps = {}
        for hp_config_file in config_files:
            if not utils.is_local_file(hp_config_file):
                raise RuntimeError(f"not found other hyperparameters config file"
                                f"({hp_config_file}) in local")

            try:
                other_hps = utils.yaml2dict(hp_config_file)
                base_hps.update(**other_hps)
            except Exception as err:
                raise RuntimeError(
                    f"other hyperparameters config file({hp_config_file}) is unvild, "
                    f"error: {err}") from err
        return base_hps
