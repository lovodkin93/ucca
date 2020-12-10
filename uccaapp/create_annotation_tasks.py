#!/usr/bin/env python3
import argparse
import sys

from tqdm import tqdm

from uccaapp.api import ServerAccessor

desc = """Create new annotation/review tasks for a specific user, given parent tokenization tasks (for creating 
annotation tasks) or parent annotation tasks (for creating review tasks) """


class AnnotationTaskCreator(ServerAccessor):
    def __init__(self, project_id=None, **kwargs):
        """
        :param project_id: Specify project for created tasks, otherwise same as parent tasks
        """
        super().__init__(**kwargs)
        if project_id is not None:
            self.set_project(project_id)

    def create_tasks(self, filename, log=None, **kwargs):
        log_h = open(log, "w", encoding="utf-8") if log else None
        lines = list(self.read_lines(filename))
        for user_id, task_id in tqdm(lines, unit="task", desc="Creating tasks"):
            task = self.create_task(**self.build_task(user_id, task_id, **kwargs))
            if log:
                print(task["id"], file=log_h, sep="\t", flush=True)
        print("Uploaded %d tasks successfully." % len(lines), file=sys.stderr)
        if log:
            log_h.close()

    def build_task(self, user_id, task_id, review=False, manager_comment=None, strict=False, **kwargs):
        del kwargs
        user = self.get_user(user_id)
        task = self.get_task(task_id)
        assert task["type"] in (["ANNOTATION", "REVIEW"] if review else ["TOKENIZATION"]), \
            "Wrong input task given: %s for task ID %s" % (task["type"], task_id)
        if strict:
            assert task["status"] == "SUBMITTED", "Parent task is not submitted: %s" % task_id
        return dict(type="REVIEW" if review else "ANNOTATION", project=self.project or task["project"], user=user,
                    passage=task["passage"], manager_comment=manager_comment or task.get("manager_comment", ""),
                    user_comment=task.get("user_comment", ""), parent=task, is_demo=False, is_active=True)

    @staticmethod
    def read_lines(filename):
        with open(filename, encoding="utf-8") as f:
            for line in f:
                fields = line.strip().split()
                try:
                    user_id, task_id = fields
                except ValueError:
                    print("Error in line: " + line.strip(), file=sys.stderr)
                    continue
                yield user_id, task_id

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filename", help="a file where each line is a <User ID> <INPUT TASK ID>, "
                                                "where the input task may be an annotation/review task "
                                                "(if given --review) or a tokenization task")
        ServerAccessor.add_arguments(argparser)
        argparser.add_argument("-r", "--review", action="store_true", help="Create annotation/review task")
        argparser.add_argument("-l", "--log", help="filename to write log of uploaded passages to")
        argparser.add_argument("--manager-comment", help="Manager comment to set for all tasks")
        ServerAccessor.add_project_id_argument(argparser)
        argparser.add_argument("-s", "--strict", action="store_true", help="Require parent task to be submitted")


def main(**kwargs):
    AnnotationTaskCreator(**kwargs).create_tasks(**kwargs)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    AnnotationTaskCreator.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
    sys.exit(0)
