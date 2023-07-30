(import click)
(import pathlib [Path])
(import dasy.cli.helpers *)
(import dasy.cli.vyper *)



(defn
  [click.group]
  cli [])


(defn
  [cli.command
   (click.option "-f" "--format" :help format-help :default "bytecode")]
  compile [filename format]
  (process-output translate-map (compile-contract filename) format OUTPUT_FORMATS))

(defn
  [cli.command
   (click.option "-n" "--name" :prompt "Enter the project name: "
              :help "Creates a new dasy project")]
  new [name]
  (setv project_folder (/ (Path.cwd) name))
    (check-n-make project_folder)
    (create-folders project_folder name)
    (create-gitignore project_folder)
    (create-ape-config project_folder name))

(when (= __name__ "__main__") (cli))
