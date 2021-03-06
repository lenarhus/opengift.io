# -*- coding:utf-8 -*-
__author__ = 'Tonakai'
from django.test import SimpleTestCase
from PManager.classes.git.diff_parser import DiffParser


class TestDiffParser(SimpleTestCase):
    def setUp(self):
        self.str = """commit 2ecec1bde6e2885073170dffcc27f3c362801019
Author: Artem Smirnov <tonakai.personal@gmail.com>
Date:   Thu Dec 11 13:49:28 2014 +0300

    test32

diff --git a/index.html b/index.html
index 7e572e5..7c7d5c6 100644
--- a/index.html
+++ b/index.html
@@ -54,3 +54,4 @@ test29
 test30
 test31
 test32
+test33"""
        self.creation_str = """commit 4487a62734c9ea1abe73316746764fb072fba504
Author: Artem Smirnov <tonakai.personal@gmail.com>
Date:   Mon Dec 15 12:52:47 2014 +0300

    Test created_file

diff --git a/tests/created_file.txt b/tests/created_file.txt
new file mode 100644
index 0000000..3c95797
--- /dev/null
+++ b/tests/created_file.txt
@@ -0,0 +1 @@
+Test file creation"""
        self.delete_str = """commit 9b1c9c7fc4648199f53ae784d90f8cdb559f7f30
Author: Artem Smirnov <tonakai.personal@gmail.com>
Date:   Mon Dec 15 12:55:09 2014 +0300

    Delete deleted_file

diff --git a/tests/deleted_file.txt b/tests/deleted_file.txt
deleted file mode 100644
index 82ebbe2..0000000
--- a/tests/deleted_file.txt
+++ /dev/null
@@ -1 +0,0 @@
-Delete this file"""
        self.move_str = """commit fb6cbca0bf8c4a1e924a2d58df8e7ace484d92a9
Author: Artem Smirnov <tonakai.personal@gmail.com>
Date:   Mon Dec 15 12:56:32 2014 +0300

    moved file

diff --git a/tests/created_file.txt b/tests/created_file.txt
deleted file mode 100644
index 3c95797..0000000
--- a/tests/created_file.txt
+++ /dev/null
@@ -1 +0,0 @@
-Test file creation
diff --git a/tests/file.txt b/tests/file.txt
new file mode 100644
index 0000000..3c95797
--- /dev/null
+++ b/tests/file.txt
@@ -0,0 +1 @@
+Test file creation^M"""
        self.multiline_comment = """commit 2aa0ea437913ec997fa25e5fb6473bccd78aa679
Author: Artem Smirnov <tonakai.personal@gmail.com>
Date:   Mon Dec 15 12:57:53 2014 +0300

    This is multiline commit message

    This is the desctiption of multiline message
    This is the third line
    Test it well
    Cause file diffs are dependent on this

diff --git a/index.html b/index.html
index 6f80cf0..e2e435a 100644
--- a/index.html
+++ b/index.html
@@ -56,3 +56,4 @@ test31
 test32
 test33
 test34
+multiline comment test"""
        self.multifile_commit = """commit 69e4e901dbc10dc17b244fdf86a50324f3e4c9c2
Author: Artem Smirnov <tonakai.personal@gmail.com>
Date:   Mon Dec 15 13:09:34 2014 +0300

    Multifile commit

diff --git a/index.html b/index.html
index e2e435a..a0ccd8e 100644
--- a/index.html
+++ b/index.html
@@ -57,3 +57,4 @@ test32
 test33
 test34
 multiline comment test
+multifile commit
diff --git a/tests/file.txt b/tests/file.txt
index 3c95797..e4f4a6d 100644
--- a/tests/file.txt
+++ b/tests/file.txt
@@ -1 +1,2 @@
 Test file creation
+multifile commit^M"""

    def test_initialization_failing(self):
        with self.assertRaises(IOError):
            DiffParser(None)

    def test_initialization_success(self):
        df = DiffParser(self.str)
        self.assertIsInstance(df, DiffParser, "Should be an instance of DiffParser")

    def test_can_return_hash(self):
        df = DiffParser(self.str)
        self.assertEqual("2ecec1bde6e2885073170dffcc27f3c362801019", df.hash)

    def test_can_return_author(self):
        df = DiffParser(self.str)
        self.assertEqual("Artem Smirnov", df.author["name"])
        self.assertEqual("tonakai.personal@gmail.com", df.author["email"])

    def test_can_return_date(self):
        df = DiffParser(self.str)
        self.assertEqual("Thu Dec 11 13:49:28 2014 +0300", df.date)

    def test_can_return_message(self):
        df = DiffParser(self.str)
        self.assertEqual("test32", df.message)

    def test_can_return_diff_files(self):
        df = DiffParser(self.str)
        self.assertEqual("/index.html", df.files[0].path)
        self.assertEqual("M", df.files[0].action)
        diff = """@@ -54,3 +54,4 @@ test29
 test30
 test31
 test32
+test33"""
        self.assertEqual(diff, df.files[0].diff)

    def test_can_return_multiline_comment(self):
        df = DiffParser(self.multiline_comment)
        msg = """This is multiline commit message

This is the desctiption of multiline message
This is the third line
Test it well
Cause file diffs are dependent on this"""
        self.assertEqual(msg, df.message)

    def test_detect_file_creation(self):
        df = DiffParser(self.creation_str)
        self.assertEqual("/tests/created_file.txt", df.files[0].path)
        self.assertEqual("C", df.files[0].action)
        diff = """@@ -0,0 +1 @@
+Test file creation"""
        self.assertEqual(diff, df.files[0].diff)

    def test_detect_file_deletion(self):
        df = DiffParser(self.delete_str)
        self.assertEqual("/tests/deleted_file.txt", df.files[0].path)
        self.assertEqual("D", df.files[0].action)
        diff = """@@ -1 +0,0 @@
-Delete this file"""
        self.assertEqual(diff, df.files[0].diff)

    def test_multifile_handling(self):
        df = DiffParser(self.move_str)
        self.assertEqual(2, len(df.files))
        self.assertEqual("/tests/created_file.txt", df.files[0].path)
        self.assertEqual("D", df.files[0].action)
        self.assertEqual("""@@ -1 +0,0 @@
-Test file creation""", df.files[0].diff)
        self.assertEqual("/tests/file.txt", df.files[1].path)
        self.assertEqual("C", df.files[1].action)
        self.assertEqual("""@@ -0,0 +1 @@
+Test file creation^M""", df.files[1].diff)

    def test_summary_for_file(self):
        df = DiffParser(self.str)
        summary = df.files[0].summary
        self.assertEqual(summary['deleted'], 0)
        self.assertEqual(summary['created'], 1)
        self.assertEqual(summary['binary'], False)

    def test_warning_commit(self):
        try:
            df = DiffParser("askldjlaksjdlaksdjlaskdjlaskjdlaksjdlaskjdlaskjdlasdjlaksjd")
            self.assertEqual(False, True)
        except IOError:
            self.assertEqual(True, True)

    def test_binary_file_handling(self):
        self.str = """commit 5cb75f0534224beed6f402352898e3d62e7df2d8
Author: gvammer <gvamm3r@gmail.com>
Date:   Thu Jan 8 14:26:16 2015 +0300

    new

diff --git a/bitrix/templates/main/js/kladr/jquery.kladr.images/spinner.png b/bitrix/templates/main/js/kladr/jquery.kladr.images/spinner.png
new file mode 100644
index 0000000..8bbafe9
Binary files /dev/null and b/bitrix/templates/main/js/kladr/jquery.kladr.images/spinner.png differ
diff --git a/bitrix/templates/main/js/kladr/jquery.kladr.js b/bitrix/templates/main/js/kladr/jquery.kladr.js
new file mode 100644
index 0000000..fdf409b
--- /dev/null
+++ b/bitrix/templates/main/js/kladr/jquery.kladr.js
@@ -0,0 +0,2 @@
+(function($) {
+    $.kladr = {};"""
        df = DiffParser(self.str)
        summary = df.files[0].summary
        self.assertEqual(summary['binary'], True)
        self.assertEqual(summary['deleted'], 0)
        self.assertEqual(summary['created'], 1)
        self.assertEqual(2, len(df.files))
        self.assertEqual("/bitrix/templates/main/js/kladr/jquery.kladr.images/spinner.png", df.files[0].path)
        self.assertEqual("/bitrix/templates/main/js/kladr/jquery.kladr.js", df.files[1].path)
        summary = df.files[1].summary
        self.assertEqual(summary['binary'], False)
        self.assertEqual(summary['deleted'], 0)
        self.assertEqual(summary['created'], 2)

    def test_empty_file_added(self):
        self.str = '''commit adc7284f7d8595b194fbeaf1afe5228a74126c48
Author: Artem Smirnov <tonakai.personal@gmail.com>
Date:   Sat Jul 25 12:55:10 2015 +0300

test6

diff --git a/test6.html b/test6.html
new file mode 100644
index 0000000..e69de29'''
        df = DiffParser(self.str)
        summary = df.files[0].summary
        self.assertEqual(summary['binary'], False)
        self.assertEqual(summary['deleted'], 0)
        self.assertEqual(summary['created'], 0)
        self.assertEqual(1, len(df.files))
        self.assertEqual("/test6.html", df.files[0].path)
        self.assertEqual(df.files[0].action, "C")

    def test_empty_file_deleted(self):
        self.str = '''commit adc7284f7d8595b194fbeaf1afe5228a74126c48
Author: Artem Smirnov <tonakai.personal@gmail.com>
Date:   Sat Jul 25 12:55:10 2015 +0300

test6

diff --git a/test6.html b/test6.html
deleted file mode 100644
index 0000000..e69de29'''
        df = DiffParser(self.str)
        summary = df.files[0].summary
        self.assertEqual(summary['binary'], False)
        self.assertEqual(summary['deleted'], 0)
        self.assertEqual(df.files[0].action, "D")
        self.assertEqual(summary['created'], 0)
        self.assertEqual(1, len(df.files))
        self.assertEqual("/test6.html", df.files[0].path)

    def test_weird_commits(self):
        self.str = '''commit 311eefd781ab75f689bf56b27ca6860981ce469f
Author: Artem Smirnov <tonakai.personal@gmail.com>
Date:   Sat Jul 25 19:01:29 2015 +0300

    Fucked up commit

diff --git a/.gitkeep b/.gitkeep
new file mode 100644
index 0000000..e69de29
diff --git a/empty file b/empty file
new file mode 100644
index 0000000..e69de29
diff --git a/empty_file b/empty_file
new file mode 100644
index 0000000..e69de29
diff --git a/file.txt b/file.txt
new file mode 100644
index 0000000..e69de29
diff --git a/xfile.txt b/xfile.txt
new file mode 100644
index 0000000..5bb7edf
--- /dev/null
+++ b/xfile.txt
@@ -0,0 +1 @@
+this is not empty'''
        df = DiffParser(self.str)
        summary = df.files[0].summary
        self.assertEqual(summary['binary'], False)
        self.assertEqual(summary['deleted'], 0)
        self.assertEqual(summary['created'], 0)
        self.assertEqual(df.files[0].action, "C")
        self.assertEqual(df.files[0].lines, [])
        self.assertEqual("/.gitkeep", df.files[0].path)

        summary = df.files[1].summary
        self.assertEqual(summary['binary'], False)
        self.assertEqual(summary['deleted'], 0)
        self.assertEqual(summary['created'], 0)
        self.assertEqual(df.files[1].action, "C")
        self.assertEqual(df.files[1].lines, [])
        self.assertEqual("/empty file", df.files[1].path)

        summary = df.files[2].summary
        self.assertEqual(summary['binary'], False)
        self.assertEqual(summary['deleted'], 0)
        self.assertEqual(summary['created'], 0)
        self.assertEqual(df.files[2].action, "C")
        self.assertEqual(df.files[2].lines, [])
        self.assertEqual("/empty_file", df.files[2].path)

        self.assertEqual(5, len(df.files))
