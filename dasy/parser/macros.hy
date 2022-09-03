(defmacro set-in [array index new-val] `(setv (subscript ~array ~index) ~new-val))
(defmacro hash-map [key-type val-type] `(subscript HashMap (tuple ~key-type ~val-type)))
(defmacro dyn-arr [type length] `(subscript DynArray (tuple ~type ~length)))
