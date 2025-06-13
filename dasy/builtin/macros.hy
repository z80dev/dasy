;; Dasy macros are syntax transformations that run at compile time
;;
;;they can make writing verbose code much more convenient. Dasy has some warts from being built around Vyper, and macros help patch over these.
;;they can also be used to implement new language features

;; some convenient type methods

(defmacro hash-map [key-type val-type]
  "(hash-map :address :string) -> (subscript HashMap '(:address :string)).
   The vyper equivalent is HashMap[address, string]"
  `(subscript HashMap (tuple ~key-type ~val-type)))

(defmacro dyn-array [type length]
  "(hash-map :address 5) -> (subscript DynArray '(:address 5)).
   The vyper equivalent is DynArray[address, 5]"
  `(subscript DynArray (tuple ~type ~length)))

(defmacro string [length] `(subscript String ~length))

(defmacro bytes [length] `(subscript Bytes ~length))

;; Field Access Macros

(defmacro set-in [obj field new-val]
  "(set-in person age 12) -> (set (. person age) 12).
   The vyper equivalent is: person.age = 12"
  `(set (. ~obj ~field) ~new-val))

(defmacro set-self [#* keys]
  (lfor k keys
        `(set (. self ~k) ~k)))

(defmacro get-at [obj #* keys]
  "(get-at person age) -> (subscript person age).
   The vyper equivalent is: person[age]"
  (let [body `(subscript ~obj ~(get keys 0))]
    (for [k (cut keys 1 None)]
      (setv body `(subscript ~body ~k)))
    body))

(defmacro get-at! [obj keys]
  (let [body `(subscript ~obj ~(get keys 0))]
    (for [k (cut keys 1 None)]
      (setv body `(subscript ~body ~k)))
    body))

(defmacro set-at [obj #* keys]
  (let [body `(subscript ~obj ~(get keys 0))]
    (for [k (cut keys 1 -1)]
      (setv body `(subscript ~body ~k)))
    `(set ~body ~(get keys -1))))

(defmacro set-at! [obj keys val]
  (let [body `(subscript ~obj ~(get keys 0))]
    (for [k (cut keys 1 None)]
      (setv body `(subscript ~body ~k)))
    `(set ~body ~val)))


;; Syntax Sugar macros
(defmacro doto [ obj #* cmds]
  `(splice ~@(lfor c cmds
         `(~(get c 0) ~obj ~@(cut c 1 None)))))

(defmacro condp [op obj #* body]
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


;; Compiler extension macros

(defmacro interface! [filename]
  (import dasy)
  (import os)
  (import pathlib [Path])
  (import dasy.parser.macro-context [get-macro-context])
  (import dasy.parser.macro-utils [compile-for-interface])
  (let [ctx (get-macro-context)
        base-dir (if ctx 
                    (. ctx base_dir) 
                    (Path (.getcwd os)))
        path (str (/ base-dir filename))
        data (compile-for-interface path)
        interface-str (.get-external-interface dasy data)]
    (.read dasy interface-str)))

(defmacro include! [filename]
  (import dasy)
  (import os)
  (import pathlib [Path])
  (import dasy.parser.macro-context [get-macro-context])
  (import dasy.parser.macro-utils [check-include-recursion get-include-stack])
  (let [ctx (get-macro-context)
        base-dir (if ctx 
                    (. ctx base_dir) 
                    (Path (.getcwd os)))
        path (str (/ base-dir filename))
        abs-path (str (.absolute (Path path)))
        include-stack (get-include-stack)]
    ;; Check for circular includes
    (check-include-recursion path)
    ;; Add to include stack
    (.add include-stack abs-path)
    (let [stream (open path)
          forms []]
      (while True
        (try
          (.append forms (.read dasy stream))
          (except [EOFError] (break))))
      ;; Remove from include stack
      (.discard include-stack abs-path)
      `(splice ~@forms))))

;; ->
(defmacro arrow [args #* body]
  ;; TODO: Get rid of this dynamic import
  (import hy.models [Expression])
  (let [[first #* rest] body
        body (if (isinstance first Expression)
                 `(~(get first 0) ~args ~@(cut first 1 None))
                 `(~first ~args))]
    (for [exp rest]
      (setv body (if (isinstance exp Expression)
                    `(~(get exp 0) ~body ~@(cut exp 1 None))
                    `(~exp ~body))))
    body))

;; ->>
(defmacro arroww [args #* body]
  (import hy.models [Expression])
  (let [[first #* rest] body
        body (if (isinstance first Expression)
                 `(~(get first 0) ~@(cut first 1 None) ~args)
                 `(~first ~args))]
    (for [exp rest]
      (setv body (if (isinstance exp Expression)
                    `(~(get exp 0) ~@(cut exp 1 None) ~body)
                    `(~exp ~body))))
    body))
