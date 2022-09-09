(defmacro set-at [array index new-val] `(setv (subscript ~array ~index) ~new-val))
(defmacro set-in [obj field new-val] `(setv (. ~obj ~field) ~new-val))
(defmacro hash-map [key-type val-type] `(subscript HashMap (tuple ~key-type ~val-type)))
(defmacro dyn-array [type length] `(subscript DynArray (tuple ~type ~length)))
(defmacro string [length] `(subscript String ~length))
(defmacro bytes [length] `(subscript Bytes ~length))
(defmacro doto [ obj #*cmds]
  (lfor c cmds
        `(~(get c 0) ~obj ~@(cut c 1 None))))
(defmacro condp [op obj #*body]
  `(cond
     ~@(lfor i (range 0 (len body))
             (if (= 0 (% i 2))
                 (if (= :else (get body i))
                     (get body i)
                     `(~op ~obj ~(get body i)))
                 (get body i)))))
