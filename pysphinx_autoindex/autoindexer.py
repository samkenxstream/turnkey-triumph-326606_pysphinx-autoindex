# coding=utf-8

import importlib
import inspect
import os


class Autoindexer(object):
    """
    Utility used to auto generate the sphinx index.rst for building documentation.

    Without this utility you will not get a full listing of your project's python class public members
    unless you manually specify each classname individually.
    """

    SKIPPED_FILENAMES = {
        '__init__.py',
        'setup.py',
        'tests'
    }

    INITIAL_MARK = 'Indices and tables'
    BEGIN_MARK = '.. pysphinx-autoindex start'
    END_MARK = '.. pysphinx-autoindex end'

    def __init__(
        self,
        project_root,
        index_rst_location,
        module_prefixes=None,
    ):
        """


        :param project_root: directory of the project root directory containing the modules
        :param index_rst_location: location of the sphinx-generated index.rst file
        :param module_prefixes: (optional) iterable of module prefixes to include in automodule discovery. For example, "proj_"
            would include the module "proj_1" and "proj_2" and all their submodules.
        """

        if not project_root or not os.path.isdir(project_root):
            raise ValueError('project_root should be a directory')

        if not index_rst_location or not os.path.isfile(index_rst_location):
            raise ValueError('index_rst_location should be a file')

        self.module_prefixes = module_prefixes or []
        self.project_root = project_root
        self.index_rst_location = index_rst_location

    def run(self):
        """
        Executes the autoindexer and writes the results to the index.rst file
        :return:
        """
        sys.path.append(self.project_root)

        self._generate_docs_index(
            self._sphinx_formatter(
                self._traverse_modules(self.project_root)
            )
        )

    def _generate_docs_index(self, sphinx_data):
        with open(self.index_rst_location, 'r') as docs_source_reader:
            docs_source = docs_source_reader.read()

        leading_chars = ''
        trailing_chars = ''
        begin_mark_location = docs_source.find(self.BEGIN_MARK)
        if begin_mark_location < 0:
            initial_mark_location = docs_source.find(self.INITIAL_MARK)
            if not initial_mark_location:
                raise ValueError('Cannot find where to write automodule, index.rst does not have {}'.format(
                    self.INITIAL_MARK
                )
            )
            replace_start = initial_mark_location
            replace_end = initial_mark_location
            trailing_chars = '\n\n'
        else:
            replace_start = begin_mark_location
            end_mark_location = docs_source.find(self.END_MARK)
            if not end_mark_location:
                raise ValueError('Corrupted index.rst file, please clear the autogenerated area under {}'.format(
                    self.BEGIN_MARK)
                )
            replace_end = end_mark_location + len(self.END_MARK)
            leading_chars = '\n'
        output_data = '{}{}{}{}{}{}{}'.format(
            docs_source[0:replace_start],
            leading_chars,
            self.BEGIN_MARK,
            sphinx_data,
            self.END_MARK,
            trailing_chars,
            docs_source[replace_end:]
        )
        self._write_index(
            output_data
        )

    def _write_index(self, data):
        with open(self.index_rst_location, 'w') as docs_source_writer:
            docs_source_writer.write(data)

    @staticmethod
    def _sphinx_formatter(modules):
        data = ''
        for mod in sorted(modules.keys()):
            classes = sorted(modules[mod])
            data += """
.. automodule:: {}
    :members: 
""".format(mod)
            for cl in classes:
                data += """
.. autoclass:: {}
    :members: 
""".format(cl)

        return data

    def _traverse_modules(self, start_dir, parent_module_name=None):
        modules = {}
        for f in os.listdir(start_dir):
            full_file = '{}/{}'.format(start_dir, f)
            if f not in self.SKIPPED_FILENAMES:
                if os.path.isdir(full_file) and os.path.isfile('{}/__init__.py'.format(full_file)):
                    module_name = f
                    if parent_module_name:
                        module_name = '{}.{}'.format(parent_module_name, module_name)
                    if self._include_module(module_name):
                        modules[module_name] = self._find_classes_in_module(module_name)
                        modules.update(self._traverse_modules(full_file, module_name))
                elif os.path.isfile(full_file) and os.path.splitext(full_file)[1] == '.py':
                    module_name = os.path.splitext(f)[0]
                    if parent_module_name:
                        module_name = '{}.{}'.format(parent_module_name, module_name)
                    modules[module_name] = self._find_classes_in_module(module_name)

        return modules

    def _find_classes_in_module(self, module_name):
        classes = set()

        try:
            imported_mod = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(imported_mod):
                if inspect.isclass(obj) and self._include_module(obj.__module__):
                    classes.add(obj.__name__)
        except Exception as ex:
            print('error finding classes in module: ' + str(ex))

        return classes

    def _include_module(self, module_name):
        if not self.module_prefixes:
            return True

        for module_prefix in self.module_prefixes:
            if module_name.startswith(module_prefix):
                return True

        return False


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: {} <project_root> <index_rst_location> [<module_prefix1>, ...]'.format(sys.argv[0]))
        sys.exit(1)

    project_root = sys.argv[1]
    index_rst_location = sys.argv[2]

    module_prefixes = None
    if len(sys.argv) >= 3:
        module_prefixes = sys.argv[3:]

    Autoindexer(
        project_root=project_root,
        index_rst_location=index_rst_location,
        module_prefixes=module_prefixes
    ).run()