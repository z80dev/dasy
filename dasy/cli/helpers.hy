(import click)
(import pathlib [Path])


(defn check-n-make [proj]
  (setv folder (Path proj))
    (if (folder.exists)
        (print (+ (str folder) " exists"))
        (folder.mkdir :exist-ok False)))


(defn create-gitignore [project_folder]
  (setv git_ignore_path (/ project_folder ".gitignore"))
  (if git_ignore_path.is-file
    (print (+ "unable to create .gitignore: " (str git_ignore_path) " file exists"))
    (do
    (git_ignore_path.touch)
    (git_ignore_path.write-text (body.lstrip)))))

(defn create-ape-config [project_folder name]
    (setv ape_config (/ project_folder "ape-config.yaml"))
    (if (ape_config.exists)
      (print (+ ape_config " exists"))
      (do
      (ape_config.write-text (+ "name " name))
      (print (+ name " is written in ape-config.yaml")))))

(defn create-folders [project_folder name]
    (for [folder_name ["contracts" "tests" "scripts"]]
      (setv folder (/ project_folder folder_name))
      (check-n-make folder)))


(setv body
        """
  # Dasy stuff
  .build/
  .cache/

  # Python
  .env
  .venv
  .pytest_cache
  .python-version
  __pycache__
  """)
