(import vyper.ast.nodes *
        hy.models [Symbol Sequence]
        hyrule.iterables [flatten])

(require
  hyrule [assoc]
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
  ;; set positional args according to node-class.__slots__
  (when args
    (setv args-zip-dict (dict (zip node-class.__slots__ args)))
    (.update args-dict args-zip-dict)
    (for [slot (list (cut node-class.__slots__ (len args) None))]
      (assoc args-dict slot None)))
  (let [node-id (.get args-dict "node_id" (next_nodeid))]
    (when (in "node_id" args-dict) (del (get args-dict "node_id")))
    (-> (node-class :node-id node-id :ast-type (. node-class __name__) #** args-dict)
        (set-parent-children (.values args-dict)))))


(defn set-parent-children [parent children]
  (for [n children]
    (branch (isinstance n it)
            list (set-parent-children parent n)
            VyperNode (do
                        (.add (. parent _children) n)
                        (setv (. n _parent) parent))))
  parent)

(defn add-src-map [src-code element ast-node]
  (when ast-node
    (if (isinstance ast-node list)
       (for [n ast-node]
         (add-src-map src-code element n))
       (do
         (setv (. ast-node full_source_code) src-code)
         (when (hasattr element "start_line")
           (do
            (setv ast-node.lineno element.start_line)
            (setv ast-node.end_lineno element.end_line)
            (setv ast-node.col_offset element.start_column)
            (setv ast-node.end_col_offset element.end_column))))))
  ast-node)

(defn process-body [body]
  (flatten
    (lfor f body
      (branch (isinstance f it)
              list f
              List (lfor f2 (. f elements)
                         (if (isinstance f2 Call)
                             (build-node Expr :value f2)
                             f2))
              Call [(build-node Expr :value f)]
              else [f]))))
