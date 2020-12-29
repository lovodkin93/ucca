#!/usr/bin/env python3
import argparse
import logging
import sys

from requests.exceptions import HTTPError
import json

from ucca.convert import to_json, to_text
from ucca.ioutil import get_passages_with_progress_bar
from uccaapp.api import ServerAccessor

try:
    from simplejson.scanner import JSONDecodeError
except ImportError:
    from json.decoder import JSONDecodeError

desc = """Convert a passage file to JSON format and upload to UCCA-App as a completed task"""

# https://github.com/omriabnd/UCCA-App/blob/master/UCCAApp_REST_API_Reference.pdf
# ucca-demo.cs.huji.ac.il or ucca.staging.cs.huji.ac.il
# upload the parse as a (completed) task:
# 0. decide which project and user you want to assign it to
# 1. POST passage (easy format)
# 2. POST task x (of type tokenization)
# 3. PUT task x (submit)
# 4. POST task y (of type annotation with parent x; this is the more complicated format)
# 5. PUT task y (submit)


class TaskUploader(ServerAccessor):
    def __init__(self, user_id, source_id, project_id, **kwargs):
        super().__init__(**kwargs)
        self.set_source(source_id)
        self.set_project(project_id)
        self.set_user(user_id)
        
    def upload_tasks(self, filenames, log=None, submit=True, existing_ids=None, **kwargs):
        del kwargs
        log_h = open(log, "w", encoding="utf-8") if log else None
        if existing_ids:
            with open(existing_ids, "r", encoding="utf-8") as ids_h:
                ids = {old_passage_id: (passage_id, tok_id, ann_id)
                       for (old_passage_id, passage_id, tok_id, ann_id)
                       in map(str.split, ids_h)}
        else:
            ids = None
        try:
            for passage in get_passages_with_progress_bar(filenames, desc="Uploading"):
                logging.debug("Uploading passage %s" % passage.ID)
                task = self.upload_task(passage, log=log_h, submit=submit, ids=ids)
                logging.debug("Submitted task %d" % task["id"])
                yield task
        except HTTPError as e:
            try:
                raise ValueError((e.response.json() if e.response else json.loads(e.args[0]))["detail"]) from e
            except JSONDecodeError:
                raise ValueError(e.response.text) from e
            finally:
                if log:
                    log_h.close()

    def upload_task(self, passage, log=None, submit=True, ids=None):
        if ids:
            passage_id, tok_id, ann_id = ids[passage.ID]
            passage_out = self.get_passage(passage_id)
            tok_user_task_out = tok_task_out = self.get_user_task(tok_id)
            ann_user_task_in = self.get_user_task(ann_id)
        else:
            passage_out = self.create_passage(text=to_text(passage, sentences=False)[0], type="PUBLIC",
                                              source=self.source, external_id=passage.ID)
            task_in = dict(type="TOKENIZATION", status="ONGOING", project=self.project, user=self.user,
                           passage=passage_out, manager_comment=passage.ID, user_comment=passage.ID, parent=None,
                           is_demo=False, is_active=True)
            tok_task_out = self.create_task(**task_in)
            tok_user_task_in = dict(tok_task_out)
            tok_user_task_in.update(to_json(passage, return_dict=True, tok_task=True))
            tok_user_task_out = self.submit_task(**tok_user_task_in)
            task_in.update(parent=tok_task_out, type="ANNOTATION")
            ann_user_task_in = self.create_task(**task_in)
        ann_user_task_in.update(
            to_json(passage, return_dict=True, tok_task=tok_user_task_out, all_categories=self.layer["categories"]))
        ann_user_task_out = self.submit_task(**ann_user_task_in, submit=submit)
        if log:
            print(passage.ID, passage_out["id"], tok_task_out["id"], ann_user_task_out["id"],
                  file=log, sep="\t", flush=True)
        return ann_user_task_out

    @staticmethod
    def add_arguments(argparser):
        argparser.add_argument("filenames", nargs="+", help="passage file names to convert and upload")
        argparser.add_argument("-l", "--log", help="filename to write log of uploaded passages to")
        argparser.add_argument("--no-submit", action="store_false", dest="submit", help="do not submit annotation task")
        argparser.add_argument("--existing-ids", help="use existing task IDs from file (output of --log); no creation")
        ServerAccessor.add_project_id_argument(argparser)
        ServerAccessor.add_source_id_argument(argparser)
        ServerAccessor.add_user_id_argument(argparser)
        ServerAccessor.add_arguments(argparser)


def main(**kwargs):
    list(TaskUploader(**kwargs).upload_tasks(**kwargs))


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description=desc)
    TaskUploader.add_arguments(argument_parser)
    main(**vars(argument_parser.parse_args()))
    sys.exit(0)
