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
(defmacro inc [target]
  `(+= ~target 1))
(defmacro dec [target]
  `(-= ~target 1))
(defmacro set-self [#* keys]
  (lfor k keys
        `(setv (. self ~k) ~k)))
(defmacro get-at [obj #* keys]
  (let [body `(subscript ~obj ~(get keys 0))]
    (for [k (cut keys 1 None)]
      (setv body `(subscript ~body ~k)))
    body))
(defmacro set-at [obj #* keys]
  (let [body `(subscript ~obj ~(get keys 0))]
    (for [k (cut keys 1 -1)]
      (setv body `(subscript ~body ~k)))
    `(setv ~body ~(get keys -1))))

(defmacro interface! [filename]
  (import dasy)
  (import os)
  (let [path (+ (.getcwd os) "/" filename)
        data (.compile-file dasy path)
        interface-str (.get-external-interface dasy data)]
    (.read dasy interface-str)))
