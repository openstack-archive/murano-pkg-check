#    Copyright (c) 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import six
import yaml

__all__ = ['YamlLoader']


class YamlMetadata(object):
    def __init__(self, mark):
        self.mark = mark

    @property
    def line(self):
        return self.mark.line

    @property
    def column(self):
        return self.mark.column

    def get_snippet(self, indent=4, max_length=75):
        return self.mark.get_snippet(indent, max_length)


class YamlObject(object):
    def __init__(self, value=None):
        self.value = value


class YamlMapping(YamlObject, dict):
    pass


class YamlSequence(YamlObject, list):
    pass


class YamlString(YamlObject, six.text_type):
    pass


class YamlNull(YamlObject):
    def __str__(self):
        return 'null'

    def __bool__(self):
        return False
    __nonzero__ = __bool__


BaseLoader = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)


class YamlLoader(BaseLoader):

    def construct_yaml_seq(self, node):
        data = YamlSequence()
        yield data
        data.extend(self.construct_sequence(node))
        data.__yaml_meta__ = node.start_mark

    def construct_yaml_str(self, node):
        value = super(YamlLoader, self).construct_yaml_str(node)
        value = YamlString(value)
        value.__yaml_meta__ = node.start_mark
        return value

    def construct_yaml_map(self, node):
        data = YamlMapping()
        yield data
        value = self.construct_mapping(node)
        data.update(value)
        data.__yaml_meta__ = node.start_mark

    def construct_yaml_null(self, node):
        value = YamlNull(node)
        value.__yaml_meta__ = node.start_mark
        return value

YamlLoader.add_constructor(
    u'tag:yaml.org,2002:seq',
    YamlLoader.construct_yaml_seq)

YamlLoader.add_constructor(
    u'tag:yaml.org,2002:str',
    YamlLoader.construct_yaml_str)

YamlLoader.add_constructor(
    u'tag:yaml.org,2002:map',
    YamlLoader.construct_yaml_map)

YamlLoader.add_constructor(
    u'tag:yaml.org,2002:null',
    YamlLoader.construct_yaml_null)
