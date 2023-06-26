(import vyper.ast.nodes *
        hy.models [Symbol Sequence]
        )
(require
  hyrule.control [case branch]
  hyrule.argmove [->])

;; (defn build-node [t #* args #** kw-args]
  ;; (t :node-id (next_nodeid) :ast-type (. t __name__) #* args #** kw-args))

(defn counter-gen []
  (setv counter 0)
  (while True
    (yield counter)
    (setv counter (+ counter 1))))

(defn next-node-id-maker []
  (setv counter (counter-gen))
  (fn []
    (next counter)))

(setv next_nodeid (next-node-id-maker))

(defn pairwise [iterable]
  (setv a (iter iterable))
        (zip a a))

(defn has-return [tree]
  (cond
    (isinstance tree Symbol) (= (str tree) "return")
    (isinstance tree Sequence) (for [el tree] (when (has-return el) (return True)))
    True (return False)))

(defn filename-to-contract-name [fname]
  ;; converts a filename to a contract name
  ;; e.g. "contracts/my_contract.vy" -> "MyContract"
  (let [words (-> fname
                    (.split "/")
                    (get -1)
                    (.split ".")
                    (get 0)
                    (.split "_"))
        capitalized_words (map (fn [word] (.capitalize word)) words)]
    (.join "" capitalized_words)))


(defn build-node [node-class #* args #** kwargs]
  (setv args-dict kwargs)
  (when args
    (do
      (for [[slot value] (zip (.__slots__ node-class) args)]
        (assoc args-dict slot value))
      (for [slot (slice (.__slots__ node-class) (len args) None)]
        (assoc args-dict slot None))
      (setv args [])))
  (setv new-node (node-class :node-id (next_nodeid) :ast-type (. node-class __name__) #* args #** args-dict))
  (set-parent-children new-node (.values args-dict))
  new-node)

(defn set-parent-children [parent children]
  (for [n children]
    (branch (isinstance n it)
          list (set-parent-children parent n)
          VyperNode (do
                      (.add (. parent _children) n)
                      (setv (. n _parent) parent)))))


(defn parse-builtin [node]
  (case (str node)
        "+" (build-node Add)
        "-" (build-node Sub)
        "*" (build-node Mult)
        "**" (build-node Pow)
        "%" (build-node Mod)
        "^" (build-node BitXor)
        "|" (build-node BitOr)
        "&" (build-node BitAnd)
        "~" (build-node Invert)
        "/" (build-node Div)
        "<" (build-node Lt :-pretty "<" :-description "less than")
        ">" (build-node Gt :-pretty ">" :-description "greater than")
        "<=" (build-node LtE :-pretty "<=" :-description "less than equal")
        ">=" (build-node GtE :-pretty ">=" :-description "greater than equal")
        "==" (build-node Eq :-pretty "==" :-description "equal")
        "!=" (build-node NotEq :-pretty "!=" :-description "not equal")
        "in" (build-node In :-pretty "in" :-description "membership")
        "notin" (build-node NotIn :-pretty "not in" :-description "exclusion")
        "not" (build-node Not :-pretty "not" :-description "negation")
        "and" (build-node And :-pretty "and" :-description "boolean and")
        "or" (build-node Or :-pretty "or" :-description "boolean or")))
