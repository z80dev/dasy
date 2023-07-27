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
  "(set-in person age 12) -> (setv (. person age) 12).
   The vyper equivalent is: person.age = 12"
  `(setv (. ~obj ~field) ~new-val))

(defmacro set-self [#* keys]
  (lfor k keys
        `(setv (. self ~k) ~k)))

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
    `(setv ~body ~(get keys -1))))

(defmacro set-at! [obj keys val]
  (let [body `(subscript ~obj ~(get keys 0))]
    (for [k (cut keys 1 None)]
      (setv body `(subscript ~body ~k)))
    `(setv ~body ~val)))


;; Syntax Sugar macros
(defmacro doto [ obj #*cmds]
  `(splice ~@(lfor c cmds
         `(~(get c 0) ~obj ~@(cut c 1 None)))))

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


;; Compiler extension macros

(defmacro interface! [filename]
  (import dasy)
  (import os)
  (let [path (+ (.getcwd os) "/" filename)
        data (.compile-file dasy path)
        interface-str (.get-external-interface dasy data)]
    (.read dasy interface-str)))

(defmacro include! [filename]
  (import dasy os)
  (let [path (+ (.getcwd os) "/" filename)
        stream (open path)
        forms []]
    (while True
      (try
        (.append forms (.read dasy stream))
        (except [EOFError] (break))))
    `(splice ~@forms)))
