(import vyper.ast.nodes *
        hy.models [Symbol Sequence])

(require
  hyrule.control [case branch]
  hyrule.argmove [->])

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

(defn add-src-map [src-code element ast-node]
  (when ast-node
    (if (isinstance ast-node list)
       (for [n ast-node]
         (add-src-map src-code element n))
       (do
         (setv (. ast-node full_source_code) src-code)
         (when (hasattr element "start_line")
           (do
             (setv (. ast-node lineno) (. element start_line))
             (setv (. ast-node end_lineno) (. element end_line))
             (setv (. ast-node col_offset) (. element start_column))
             (setv (. ast-node end_col_offset) (. element end_column)))))))
  ast-node)

(defn process-body [body]
  (setv new-body [])
  (for [f body]
    (cond
      (isinstance f list) (for [f2 f] (.append new-body f2))
      (isinstance f List) (for [f2 (. f elements)]
                            (cond
                              (isinstance f2 Call) (.append new-body (build-node Expr :value f2))
                              True (.append new-body f2)))
      (isinstance f Call) (.append new-body (build-node Expr :value f))
      True (.append new-body f)))
  new-body)
