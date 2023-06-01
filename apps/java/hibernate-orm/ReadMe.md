The hibernate-orm JPA tests are currently marked as broken because we currently do not support the fcntl SETLK and SETLKW commands for file locking.

To run the tests, the following changes can be made to get the tests running. This  is not a permanent solution but this will get the tests running until the functionality is implemented in enclaveos completely.


diff --git a/shim/src/sys/shim_fcntl.c b/shim/src/sys/shim_fcntl.c
index b4338ec..9f3b903 100644
--- a/shim/src/sys/shim_fcntl.c
+++ b/shim/src/sys/shim_fcntl.c
@@ -166,9 +166,10 @@ int shim_do_fcntl (int fd, int cmd, unsigned long arg)
 #else
             // Should we return EINVAL to indicate we do not support this
             // operation.
-            ret = -ENOSYS;
 #endif
-            UNSUPPORTED_ONCE("F_SETLK");
+            ret = 0;
             break;

         /* F_SETLKW (struct flock *)
@@ -179,8 +180,9 @@ int shim_do_fcntl (int fd, int cmd, unsigned long arg)
          *   set to EINTR; see signal(7)).
          */
         case F_SETLKW:
-            ret = -ENOSYS;
-            UNSUPPORTED_ONCE("F_SETLKW");
+            ret = 0;
             break;

         /* F_GETLK (struct flock *)

