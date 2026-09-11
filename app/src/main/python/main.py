import socket
from multiprocessing import Process
from flask import Flask, request, session, redirect, send_file, jsonify
import os
from urllib.parse import quote
from datetime import datetime
import shutil
from natsort import natsorted
process = None
website_password = None
app = Flask("Local File Sharing")
current_folder_path = "/storage/emulated/0"
@app.before_request
def before_request():
    if request.method == "GET":
        if request.path not in ["/login", "/home"]:
            return redirect("/login")
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("logged_in"):
            return redirect("/home?path=" + quote(current_folder_path))
        else:
            login_html = """<!DOCTYPE html>
<html>
    <head>
        <title>Local File Sharing</title>
    </head>
    <body style="font-family: Arial; margin: 0; background-color: #f5f6fa">
        <header style="font-size: 24px; background-color: #1f2937; color: white; font-weight: bold; padding: 16px 32px">Local File Sharing</header>
        <div style="height: calc(100vh - 60px); display: flex; justify-content: center; align-items: center">
            <div style="border-radius: 8px; background-color: white; padding: 30px; width: 300px; display: flex; align-items: center; justify-content: center; flex-direction: column; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1)">
                <h2 style="margin-bottom: 20px">Login</h2>
                <form id="DataForm" style="width: 100%">
                    <input id="password" type="password" name="password" placeholder="Enter password" required style="width: 100%; padding: 10px; border-radius: 5px; border-width: 1px; border-color: #ccc; border-style: solid; margin-bottom: 20px; box-sizing: border-box">
                    <button style="padding: 10px; background-color: #3b82f6; border-radius: 5px; border: none; font-size: 15px; color: white; cursor: pointer; width: 100%" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Login</button>
                </form>
            </div>
        </div>
    </body>
    <script>
        const DataForm = document.getElementById("DataForm")
        const password = document.getElementById("password")
        function EnableForm(form) {
            for (let element of form.elements) {
                element.disabled = false
            }
        }
        function DisableForm(form) {
            for (let element of form.elements) {
                element.disabled = true
            }
        }
        DataForm.addEventListener("submit", async function(event) {
            event.preventDefault()
            DisableForm(DataForm)
            const package = new FormData()
            package.append("password", password.value)
            fetch("/login", {method: "POST", body: package}).then(async function(response) {
                if (response.status == 200) {
                    window.location.href = await response.text()
                }
                else if (response.status == 301) {
                    alert("Incorrect password")
                    EnableForm(DataForm)
                }
                else {
                    alert("An unknown error occured")
                    EnableForm(DataForm)
                }
            })
        })
    </script>
</html>"""
            return login_html
    else:
        try:
            if request.form.get("password") == website_password:
                session["logged_in"] = True
                return "/home?path=" + quote(current_folder_path)
            else:
                return "", 301
        except:
            return "", 300
@app.route("/get_dirname", methods=["POST"])
def get_dirname():
    try:
        if session["logged_in"]:
            return os.path.dirname(request.form.get("path"))
        else:
            return "", 300
    except:
        return "", 300
@app.route("/verify_path", methods=["POST"])
def verify_path():
    try:
        if session["logged_in"]:
            if os.path.exists(request.form.get("path")):
                return ""
            else:
                return "", 301
        else:
            return "", 300
    except:
        return "", 300
@app.route("/get_path", methods=["POST"])
def get_path():
    try:
        if session.get("logged_in"):
            return session.get("source_path")
        else:
            return "", 300
    except:
        return "", 300
@app.route("/actions", methods = ["POST"])
def actions():
    try:
        if session["logged_in"]:
            request_type = request.args.get("type")
            if request_type == "download":
                return send_file(request.form.get("path"), as_attachment=True)
            elif request_type == "rename":
                path = request.form.get("path")
                new_path = os.path.join(os.path.dirname(path) + "/" + request.form.get("new_name"))
                os.rename(path, new_path)
                return ""
            elif request_type == "copy_set":
                session["source_path"] = "Copy:" + request.form.get("path")
                return ""
            elif request_type == "copy":
                currentfolderpath = request.form.get("current_folder_path")
                source_path = session.get("source_path").removeprefix("Copy:")
                session.pop("source_path")
                try:
                    if os.path.isdir(source_path):
                        destination_path = currentfolderpath + "/" + source_path.split("/")[-1] + " (Copy)"
                        if os.path.exists(destination_path):
                            return destination_path.removeprefix(currentfolderpath + "/"), 301
                        else:
                            shutil.copytree(source_path, destination_path)
                    else:
                        destination_path = currentfolderpath + "/" + source_path.split("/")[-1].split(".")[0] + " (Copy)" + "." + source_path.split("/")[-1].split(".")[1]
                        if os.path.exists(destination_path):
                            return destination_path.removeprefix(currentfolderpath + "/"), 301
                        else:
                            shutil.copy(source_path, currentfolderpath + "/" + source_path.split("/")[-1].split(".")[0] + " (Copy)" + "." + source_path.split("/")[-1].split(".")[1])
                    return ""
                except:
                    return "", 300
            elif request_type == "mass_copy_set":
                session["source_path"] = "MassCopy:" + str(request.form.get("paths"))
                return ""
            elif request_type == "mass_copy":
                currentfolderpath = request.form.get("current_folder_path")
                source_paths = session.get("source_path").removeprefix("MassCopy:").split(",")
                session.pop("source_path")
                failed = []
                for source_path in source_paths:
                    try:
                        if os.path.isdir(source_path):
                            new_folder_name = source_path.split("/")[-1] + " (Copy)"
                            destination_path = currentfolderpath + "/" + new_folder_name
                            if os.path.exists(destination_path):
                                failed.append(new_folder_name + ": Already exists in this folder")
                            else:
                                shutil.copytree(source_path, destination_path)
                        else:
                            new_file_name = source_path.split("/")[-1].split(".")[0] + " (Copy)" + "." + source_path.split("/")[-1].split(".")[1]
                            destination_path = currentfolderpath + "/" + new_file_name
                            if os.path.exists(destination_path):
                                failed.append(new_file_name + ": Already exists in this folder")
                            else:
                                shutil.copy(source_path, destination_path)
                    except:
                        failed.append(source_path.split("/")[-1] + ": An unkown error occured")
                if len(failed) == 0:
                    return ""
                else:
                    return jsonify(failed), 301
            elif request_type == "move_set":
                session["source_path"] = "Move:" + request.form.get("path")
                return ""
            elif request_type == "move":
                source_path = session.get("source_path").removeprefix("Move:")
                session.pop("source_path")
                currentfolderpath = request.form.get("current_folder_path")
                if os.path.exists(currentfolderpath + "/" + source_path.split("/")[-1]):
                    return source_path.split("/")[-1], 301
                else:
                    shutil.move(source_path, currentfolderpath)
                    return ""
            elif request_type == "mass_move_set":
                session["source_path"] = "MassMove:" + str(request.form.get("paths"))
                return ""
            elif request_type == "mass_move":
                currentfolderpath = request.form.get("current_folder_path")
                source_paths = session.get("source_path").removeprefix("MassMove:").split(",")
                session["source_path"] = ""
                failed = []
                for source_path in source_paths:
                    file_name = source_path.split("/")[-1]
                    try:
                        if os.path.exists(currentfolderpath + "/" + file_name):
                            failed.append(file_name + ": This file / folder already exists in this folder")
                        else:
                            shutil.move(source_path, currentfolderpath)
                    except:
                        failed.append(file_name + ": An unknown error occured")
                if len(failed) == 0:
                    return ""
                else:
                    return jsonify(failed), 301
            elif request_type == "delete":
                path = request.form.get("path")
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return ""
            elif request_type == "mass_delete":
                failed = []
                for path in request.form.get("paths").split(","):
                    try:
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                    except:
                        failed.append(path.split("/")[-1])
                if len(failed) == 0:
                    return ""
                else:
                    return jsonify(failed), 301
        else:
            return "", 300
    except:
        return "", 300
def FormattedSize(bytes):
    if bytes < 1000:
        return f"{bytes} B"
    elif bytes < 1000**2:
        return f"{bytes / 1000:.2f} KB"
    elif bytes < 1000**3:
        return f"{bytes / 1000**2:.2f} MB"
    else:
        return f"{bytes / 1000**3:.2f} GB"
@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        if not "logged_in" in session:
            return redirect("/login")
        else:
            if session["logged_in"]:
                global current_folder_path
                path = request.args.get("path")
                if path:
                    current_folder_path = path
                    home_html = """<!DOCTYPE html>
<html>
    <head>
        <title>Local File Sharing</title>
    </head>
    <body style="font-family: Arial; margin: 0; background-color: #f5f6fa">
        <div id = "SelectionBox" style="position: absolute; border: 1px solid #3399ff; background-color: rgba(51, 153, 255, 0.35); display: none; top: 0px; left: 0px"></div>
        <header style="font-size: 24px; background-color: #1f2937; color: white; font-weight: bold; padding: 16px 32px">Local File Sharing</header>
        <div style="margin: 24px 32px 15px 32px; display: flex; justify-content: center; align-items: center; gap: 8px">
            <button id="UpButton" style="padding: 8px; border-radius: 5px; border: none; background-color: #3b82f6; color: white; cursor: pointer; width: 50px" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">⬆</button>
            <input id="CurrentFolderPath" type="text" value="CurrentFolderPathFromPython" style="flex: 1; padding: 8px; border-radius: 5px; border-width: 1px; border-style: solid; border-color: #ccc; height: 18px; font-size: 16px">
            <div style="position: relative">
                <button id="UploadButton" style="padding: 8px; border-radius: 5px; border: none; background-color: #f97316; color: white; cursor: pointer; width: 100px" onmouseover="this.style.background='#ea580c'" onmouseout="this.style.background='#f97316'">Upload</button>
                <div id="UploadMenu" style="display: none; position: absolute; top: 32px; width: 100%; background-color: white; box-shadow: -4px 4px 10px rgba(0, 0, 0, 0.1); border-radius: 5px; z-index: 1">
                    <div style="padding: 8px; cursor: pointer" onclick="FilesInputSection.click()" onmouseover="this.style.background='#f4f4f4'" onmouseout="this.style.background='white'">Upload File</div>
                    <div style="padding: 8px; cursor: pointer" onclick="FolderInputSection.click()" onmouseover="this.style.background='#f4f4f4'" onmouseout="this.style.background='white'">Upload Folder</div>
                </div>
            </div>
        </div>
        <input id="SearchBar" type="text" placeholder="Search" style="margin: 0px 32px 15px 32px; width: calc(100% - 82px); padding: 8px; border-radius: 5px; border-width: 1px; border-style: solid; border-color: #ccc; height: 18px; font-size: 16px">
        <div id="ProgressBarContainer" style="position: relative; background-color: #e5e7eb; display: none; margin: 0px 32px 15px 32px; border-radius: 5px; height: 20px; z-index: 0">
            <div id="ProgressBar" style="background-color: #83e559; width: 0%; height: 100%; border-radius: 5px"></div>
            <div id="ProgressPercentage" style="position: absolute; top: 0; height: 100%; width: 100%; display: flex; align-items: center; justify-content: center">0%</div>
        </div>
        <button id="CopyMoveButton" style="display: DisplayFromPython; margin: 0px 0px 15px 32px; padding: 10px 12px; background-color: #4caf50; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer" onmouseover="this.style.background='#45a049'" onmouseout="this.style.background='#4CAF50'">TextFromPython</button>
        <div id="MassActionButtons" style="margin: 0px 0px 15px 32px; visibility: hidden">
            <button id="MassActionDownloadButton" style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #10b981; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#059669'" onmouseout="this.style.background='#10b981'">Download</button>
            <button id="MassActionRenameButton" style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #ffce50; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#f59e0b'" onmouseout="this.style.background='#fbbf24'">Rename</button>
            <button id="MassActionCopyButton" style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #3b82f6; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Copy</button>
            <button id="MassActionMoveButton" style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #6366f1; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#4f46e5'" onmouseout="this.style.background='#6366f1'">Move</button>
            <button id="MassActionDeleteButton" style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #ef4444; color: white; cursor: pointer; margin-right: 15px" onmouseover="this.style.background='#b91c1c'" onmouseout="this.style.background='#ef4444'">Delete</button>
            <span id="SelectedItemsCounter" style="font-weight: bold">Selected items:</span>
        </div>
        <input type="file" id="FilesInputSection" style="display: none" multiple name="FilesInputSection">
        <input type="file" id="FolderInputSection" style="display: none" webkitdirectory name="FolderInputSection">
        <div style="margin: 0px 32px 0px 32px; border-top-left-radius: 5px; border-top-right-radius: 5px">
            <div style="display: flex; flex-direction: row; background-color: #e5e7eb; padding: 12px">
                <span style="width: 400px; font-weight: bold">Name</span>
                <span style="width: 250px; font-weight: bold">Last modified</span>
                <span style="width: 140px; font-weight: bold">Size</span>
                <span style="font-weight: bold">Actions</span>
            </div>
            <div id="FilesList"></div>
        </div>
FilesFromFolderFromPython
        <div id="NoResults" style="display: none; justify-content: center; align-items: center; height: 500px">
            <div style="background-color: #f9fafb; color: #374151; padding: 20px 30px; border-radius: 8px; font-size: 18px; font-weight: bold; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1)">No results</div>
        </div>
    </body>
    <script>
        let x = 0
        let y = 0
        const SelectionBox = document.getElementById("SelectionBox")
        document.addEventListener("mousedown", function (event) {
            if (event.button == 0 && event.target.tagName == "BODY") {
                if (SelectionBox.style.display == "none") {
                    SelectionBox.style.top = event.pageY + "px"
                    SelectionBox.style.left = event.pageX + "px"
                    SelectionBox.style.width = "0px"
                    SelectionBox.style.height = "0px"
                    SelectionBox.style.display = "block"
                    x = event.pageX
                    y = event.pageY
                    document.body.style.userSelect = "none"
                }
            }
        })
        document.addEventListener("mouseup", function(event) {
            if (event.button === 0) {
                SelectionBox.style.display = "none"
                document.body.style.userSelect = "auto"
            }
        })
        function overlapping(selection_box, div_rect) {
            return !(selection_box.right < div_rect.left || selection_box.left > div_rect.right || selection_box.bottom < div_rect.top || selection_box.top > div_rect.bottom)
        }
        const FilesList = document.getElementById("FilesList")
        document.addEventListener("mousemove", function (event) {
            if (SelectionBox.style.display == "block") {
                const left = Math.min(x, event.pageX)
                const top = Math.min(y, event.pageY)
                let width = Math.abs(event.pageX - x)
                let height = Math.abs(event.pageY - y)
                const PageWidth = document.body.offsetWidth - 2
                const PageHeight = document.body.offsetHeight - 2
                if (left + width > PageWidth) {
                    width = PageWidth - left
                }
                if (top + height > PageHeight) {
                    height = PageHeight - top
                }
                SelectionBox.style.top = top + "px"
                SelectionBox.style.left = left + "px"
                SelectionBox.style.width = width + "px"
                SelectionBox.style.height = height + "px"
                if (event.clientY < 20) {
                    window.scrollBy(0, -20)
                } else if (event.clientY > window.innerHeight - 20) {
                    window.scrollBy(0, 20)
                }
                const file_elements = FilesList.children
                for (let i = 0; i < file_elements.length; i++) {
                    if (overlapping(SelectionBox.getBoundingClientRect(), file_elements[i].getBoundingClientRect())) {
                        const checkbox = file_elements[i].children[0].children[0]
                        if (!checkbox.checked) {
                            checkbox.checked = true
                            checkbox.style.opacity = 1
                            checkbox.dispatchEvent(new Event("change", {bubbles: true}))
                        }
                    }
                }
            }
        })
        let SelectionMode = "Select All"
        document.addEventListener("keydown", function (event) {
            if (document.activeElement.id != "SearchBar" && document.activeElement.id != "CurrentFolderPath") {
                event.preventDefault()
                let temp_file_elements = FilesList.children
                let file_elements = []
                for (let i = 0; i < temp_file_elements.length; i++) {
                    if (temp_file_elements[i].style.display != "none") {
                        file_elements.push(temp_file_elements[i])
                    }
                }
                temp_file_elements = []
                if (event.ctrlKey && event.key == "a") {
                    if (SelectionMode == "Select All") {
                        for (let i = 0; i < file_elements.length; i++) {
                            const checkbox = file_elements[i].children[0].children[0]
                            if (!checkbox.checked) {
                                checkbox.checked = true
                                checkbox.style.opacity = 1
                                checkbox.dispatchEvent(new Event("change", {bubbles: true}))
                            }
                        }
                        SelectionMode = "Deselect All"
                    }
                    else {
                        for (let i = 0; i < file_elements.length; i++) {
                            const checkbox = file_elements[i].children[0].children[0]
                            if (checkbox.checked) {
                                checkbox.checked = false
                                checkbox.style.opacity = 0
                                checkbox.dispatchEvent(new Event("change", {bubbles: true}))
                            }
                        }
                        SelectionMode = "Select All"
                    }
                }
                else if (event.ctrlKey && event.key == "A") {
                    for (let i = 0; i < file_elements.length; i++) {
                        const checkbox = file_elements[i].children[0].children[0]
                        if (checkbox.checked) {
                            checkbox.checked = false
                            checkbox.style.opacity = 0
                        }
                        else {
                            checkbox.checked = true
                            checkbox.style.opacity = 1
                        }
                        checkbox.dispatchEvent(new Event("change", {bubbles: true}))
                    }
                }
            }
        })
        const CurrentFolderPath = document.getElementById("CurrentFolderPath")
        document.getElementById("UpButton").onclick = function() {
            while (CurrentFolderPath.value.includes("//")) {
                CurrentFolderPath.value = CurrentFolderPath.value.replace("//", "/")
            }
            if (CurrentFolderPath.value.endsWith("/")) {
                CurrentFolderPath.value = CurrentFolderPath.value.substring(0, CurrentFolderPath.value.length - 1)
            }
            const package = new FormData()
            package.append("path", CurrentFolderPath.value)
            fetch("/get_dirname", {method: "POST", body: package}).then(async function(response) {
                if (response.status == 200) {
                    window.location.href = "/home?path=" + encodeURIComponent(await response.text())
                }
                else {
                    alert("An unknown error occured")
                }
            })
        }
        CurrentFolderPath.addEventListener("keydown", function(event) {
            if (event.key == "Enter") {
                while (CurrentFolderPath.value.includes("//")) {
                    CurrentFolderPath.value = CurrentFolderPath.value.replace("//", "/")
                }
                if (CurrentFolderPath.value.endsWith("/")) {
                    CurrentFolderPath.value = CurrentFolderPath.value.substring(0, CurrentFolderPath.value.length - 1)
                }
                const package = new FormData()
                package.append("path", CurrentFolderPath.value)
                fetch("/verify_path", {method: "POST", body: package}).then(function(response) {
                    if (response.status == 200) {
                        window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value)
                    }
                    else if (response.status == 301) {
                        alert("Invalid Path")
                    }
                    else {
                        alert("An unknown error occured")
                    }
                })
            }
        })
        const UploadMenu = document.getElementById("UploadMenu")
        document.getElementById("UploadButton").onclick = function() {
            if (UploadMenu.style.display == "none") {
                UploadMenu.style.display = "block"
            } else {
                UploadMenu.style.display = "none"
            }
        }
        document.addEventListener("click", function(event) {
            if (!UploadButton.contains(event.target) && !UploadMenu.contains(event.target)) {
                UploadMenu.style.display = "none"
            }
        })
        const SearchBar = document.getElementById('SearchBar')
        const NoResults = document.getElementById('NoResults')
        SearchBar.addEventListener('input', function() {
            file_elements = FilesList.children
            hidden_files = 0
            query = SearchBar.value.trim().toLowerCase()
            if (query == "") {
                for (let i = 0; i < file_elements.length; i++) {
                    file_elements[i].style.display = "flex"
                }
            }
            else {
                for (let i = 0; i < file_elements.length; i++) {
                    if (file_elements[i].children[0].textContent.replace(file_elements[i].children[0].children[1].textContent, "").trim().toLowerCase().includes(query)) {
                        file_elements[i].style.display = "flex"
                    }
                    else {
                        file_elements[i].style.display = "none"
                        hidden_files += 1
                    }
                }
                if (hidden_files == file_elements.length) {
                    NoResults.style.display = "flex"
                }
                else {
                    NoResults.style.display = "none"
                }
            }
        })
        const ProgressBarContainer = document.getElementById("ProgressBarContainer")
        const ProgressBar = document.getElementById("ProgressBar")
        const ProgressPercentage = document.getElementById("ProgressPercentage")
        function UpdateProgressBar(percentage) {
            ProgressBar.style.width = percentage + "%"
            ProgressPercentage.textContent = percentage + "%"
        }
        const CopyMoveButton = document.getElementById("CopyMoveButton")
        CopyMoveButton.onclick = function() {
            fetch("/get_path", {method: "POST"}).then(async function(response) {
                let action = ""
                let action_string = ""
                const ResponseText = await response.text()
                if (ResponseText.startsWith("Copy")) {
                    action = "copy"
                    action_string = "copying"
                    CopyMoveButton.textContent = "Copying..."
                }
                else if (ResponseText.startsWith("MassCopy")) {
                    action = "mass_copy"
                    action_string = "copying"
                    CopyMoveButton.textContent = "Copying..."
                }
                else if (ResponseText.startsWith("MassMove")) {
                    action = "mass_move"
                    action_string = "copying"
                    CopyMoveButton.textContent = "Moving"
                }
                else {
                    action = "move"
                    action_string = "moving"
                    CopyMoveButton.textContent = "Moving..."
                }
                const package = new FormData()
                package.append("current_folder_path", CurrentFolderPath.value)
                fetch("/actions?type=" + action, {method: "POST", body: package}).then(async function(response) {
                    if (response.status == 200) {
                        alert("Completed " + action_string + " all files / folders")
                    }
                    else if (response.status == 301) {
                        if (action.startsWith("mass")) {
                            const failed_files = await response.json()
                            alert("An error was encountered while " + action_string + " the following files / folders:\\n" + failed_files.join("\\n"))
                        }
                        else {
                            const duplicate_file = await response.text()
                            alert("The file / folder " + duplicate_file + " already exists in this folder")
                        }
                    }
                    else {
                        alert("An unknown error occured")
                    }
                    window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value)
                })
            })
        }
        let uploading = false
        function UploadFiles(files) {
            if (uploading) {
                alert("An upload is already under progress, please wait until it is over")
            }
            else {
                uploading = true
                if (files.length != 0) {
                    ProgressBarContainer.style.display = "block"
                    const package = new FormData()
                    for (let file of files) {
                        package.append("Files", file)
                    }
                    const xhr = new XMLHttpRequest()
                    while (CurrentFolderPath.value.includes("//")) {
                        CurrentFolderPath.value = CurrentFolderPath.value.replace("//", "/")
                    }
                    if (CurrentFolderPath.value.endsWith("/")) {
                        CurrentFolderPath.value = CurrentFolderPath.value.substring(0, CurrentFolderPath.value.length - 1)
                    }
                    xhr.open('POST', '/home?path=' + CurrentFolderPath.value, true)
                    xhr.upload.onprogress = function(event) {
                        if (event.lengthComputable) {
                            UpdateProgressBar(Math.round((event.loaded / event.total) * 100))
                        }
                    }
                    xhr.onload = function() {
                        if (xhr.status == 200) {
                            UpdateProgressBar(100)
                            alert("Upload completed")
                        } else {
                            alert("An unknown error occured")
                        }
                        uploading = false
                        UpdateProgressBar(0)
                        ProgressBarContainer.style.display = "none"
                        window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value)
                    }
                    xhr.send(package)
                }
            }
        }
        const FilesInputSection = document.getElementById('FilesInputSection')
        const FolderInputSection = document.getElementById('FolderInputSection')
        FilesInputSection.addEventListener('change', function() {
            UploadFiles(FilesInputSection.files)
        })
        FolderInputSection.addEventListener('change', function() {
            UploadFiles(FolderInputSection.files)
        })
        document.querySelectorAll("file").forEach(function(file) {
            const file_element_icon = file.getAttribute("icon")
            const file_element_name = file.getAttribute("name")
            const file_element_last_modified = file.getAttribute("last_modified")
            const file_element_size = file.getAttribute("size")
            const file_element = document.createElement("div")
            file_element.style.cssText = "background-color: white; display: flex; align-items: center; flex-direction: row; padding: 12px; border-bottom: 1px solid #ddd"
            let inner_html = `<div style="display: flex; align-items: center; width: 400px">
    <input type="checkbox" style="display: block; opacity: 0; transition: opacity 0.2s; margin-right: 8px">
    <span style="font-size: 24px; margin-right: 8px">${file_element_icon}</span>
    ${file_element_name}
</div>
<span style="width: 250px">${file_element_last_modified}</span>
<span style="width: 140px">${file_element_size}</span>
<button style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #10b981; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#059669'" onmouseout="this.style.background='#10b981'">Download</button>
<button style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #ffce50; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#f59e0b'" onmouseout="this.style.background='#fbbf24'">Rename</button>
<button style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #3b82f6; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">Copy</button>
<button style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #6366f1; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#4f46e5'" onmouseout="this.style.background='#6366f1'">Move</button>
<button style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #ef4444; color: white; cursor: pointer" onmouseover="this.style.background='#b91c1c'" onmouseout="this.style.background='#ef4444'">Delete</button>`
            if (file_element_icon == "📁") {
                inner_html = inner_html.replace(`<button style="padding: 6px 12px; font-size: 15px; border-radius: 6px; border: none; background-color: #10b981; color: white; cursor: pointer; margin-right: 4px" onmouseover="this.style.background='#059669'" onmouseout="this.style.background='#10b981'">Download</button>`, "")
            }
            file_element.innerHTML = inner_html
            const checkbox = file_element.children[0].children[0]
            file_element.onmouseover = function() {
                file_element.style.background = "#f9fafb"
                if (!checkbox.checked) {
                    checkbox.style.opacity = 1
                }
            }
            file_element.onmouseout = function() {
                file_element.style.background = "white"
                if (!checkbox.checked) {
                    checkbox.style.opacity = 0
                }
            }
            FilesList.appendChild(file_element)
        })
        const MassActionButtons = document.getElementById("MassActionButtons")
        const MassActionDownloadButton = document.getElementById("MassActionDownloadButton")
        const MassActionRenameButton = document.getElementById("MassActionRenameButton")
        const MassActionCopyButton = document.getElementById("MassActionCopyButton")
        const MassActionMoveButton = document.getElementById("MassActionMoveButton")
        const MassActionDeleteButton = document.getElementById("MassActionDeleteButton")
        let checked_files = []
        const SelectedItemsCounter = document.getElementById("SelectedItemsCounter")
        FilesList.addEventListener("change", function(event) {
            if (event.target.type == "checkbox") {
                const checkbox = event.target
                const inner_div = checkbox.parentElement
                const file_icon = inner_div.children[1].textContent
                const file_name = inner_div.textContent.replace(file_icon, "").trim()
                const file_key = file_icon + " " + file_name
                if (checkbox.checked) {
                    checked_files.push(file_icon + " " + file_name)
                }
                else {
                    checked_files.splice(checked_files.indexOf(file_icon + " " + file_name), 1)
                }
                if (checked_files.length == 0) {
                    MassActionButtons.style.visibility = "hidden"
                    SelectedItemsCounter.textContent = "Selected Items:"
                } else {
                    MassActionButtons.style.visibility = "visible"
                    SelectedItemsCounter.textContent = "Selected Items: " + checked_files.length
                }
                if (checked_files.length == 1) {
                    MassActionRenameButton.style.display = "inline-block"
                } else {
                    MassActionRenameButton.style.display = "none"
                }
                MassActionDownloadButton.style.display = "inline-block"
                for (let i = 0; i < checked_files.length; i++) {
                    if (checked_files[i].startsWith("📁")) {
                        MassActionDownloadButton.style.display = "none"
                        break
                    }
                }
            }
        })
        MassActionDownloadButton.onclick = function() {
            MassActionDownloadButton.disabled = true
            const file_elements = FilesList.children
            for (let i=0; i<checked_files.length; i++) {
                for (let j=0; j<file_elements.length; j++) {
                    const inner_div = file_elements[j].children[0]
                    const file_icon = inner_div.children[1].textContent
                    const file_name = inner_div.textContent.replace(file_icon, "").trim()
                    if (file_name == checked_files[i].split(" ").splice(1).join(" ")) {
                        setTimeout(function() {
                            file_elements[j].children[3].click()
                            if (i == checked_files.length - 1) {
                                MassActionDownloadButton.disabled = false
                            }
                        }, 200 * i)
                        break
                    }
                }
            }
        }
        MassActionRenameButton.onclick = function() {
            const file_name = checked_files[0].split(" ").splice(1).join(" ")
            const file_elements = FilesList.children
            for (let i=0; i<file_elements.length; i++) {
                const inner_div = file_elements[i].children[0]
                const file_element_icon = inner_div.children[1].textContent
                const file_element_name = inner_div.textContent.replace(file_element_icon, "").trim()
                if (file_element_name == file_name) {
                    file_elements[i].children[4].click()
                    break
                }
            }
        }
        MassActionCopyButton.onclick = function() {
            let paths = []
            for (let i=0; i<checked_files.length; i++) {
                paths.push(CurrentFolderPath.value + "/" + checked_files[i].split(" ").splice(1).join(" "))
            }
            const package = new FormData()
            package.append("paths", paths)
            fetch("/actions?type=mass_copy_set", {method: "POST", body: package}).then(function(response) {
                if (response.status == 200) {
                    CopyMoveButton.textContent = "Paste here"
                    CopyMoveButton.style.display = "block"
                    alert("Copied files. Go to the folder where you want to paste these to then click move")
                }
                else {
                    alert("An unknown error occured")
                }
            })
        }
        MassActionMoveButton.onclick = function() {
            let paths = []
            for (let i=0; i<checked_files.length; i++) {
                paths.push(CurrentFolderPath.value + "/" + checked_files[i].split(" ").splice(1).join(" "))
            }
            const package = new FormData()
            package.append("paths", paths)
            fetch("/actions?type=mass_move_set", {method: "POST", body: package}).then(function(response) {
                if (response.status == 200) {
                    CopyMoveButton.textContent = "Move here"
                    CopyMoveButton.style.display = "block"
                    alert("Copied files. Go to the folder where you want to move these to then click move")
                }
                else {
                    alert("An unknown error occured")
                }
            })
        }
        MassActionDeleteButton.onclick = function() {
            let paths = []
            for (let i=0; i<checked_files.length; i++) {
                paths.push(checked_files[i].split(" ").splice(1).join(" "))
            }
            if (confirm(`Are you sure you want to delete the following files:\\n` + paths.join(`\\n`))) {
                paths = []
                for (let i = 0; i<checked_files.length; i++) {
                    paths.push(CurrentFolderPath.value + "/" + checked_files[i].split(" ").splice(1).join(" "))
                }
                const package = new FormData()
                package.append("paths", paths)
                fetch("/actions?type=mass_delete", {method: "POST", body: package}).then(async function(response) {
                    if (response.status == 200) {
                            alert("Deleted all files / folders")
                    }
                    else if (response.status == 301) {
                        const failed_files = await response.json()
                        alert(`Failed to delete the following files / folders:\\n` + failed_files.join(`\\n`))
                    }
                    else {
                        alert("An unknown error occured")
                    }
                    window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value)
                })
            }
        }
        FilesList.addEventListener("click", function(event) {
            let div = event.target.closest("div")
            if (window.getComputedStyle(div).padding != "12px") {
                div = div.parentElement
            }
            const inner_div = div.children[0]
            const file_icon = inner_div.children[1].textContent
            const file_name = inner_div.textContent.replace(file_icon, "").trim()
            if (event.target.tagName == "BUTTON") {
                if (event.target.textContent == "Download") {
                    const package = new FormData()
                    package.append("path", CurrentFolderPath.value + "/" + file_name)
                    fetch("/actions?type=download", {method: "POST", body: package}).then(function(response) {
                        if (response.status == 200) {
                            const new_package = document.createElement("form")
                            new_package.method = "POST"
                            new_package.action = "/actions?type=download"
                            const path = document.createElement("input")
                            path.name = "path"
                            path.value = CurrentFolderPath.value + "/" + file_name
                            new_package.appendChild(path)
                            document.body.appendChild(new_package)
                            new_package.submit()
                            document.body.removeChild(new_package)
                        }
                        else {
                            alert("An unknown error occured")
                        }
                    })
                }
                else if (event.target.textContent == "Rename") {
                    const new_name = prompt(`Enter the new name (include file extension)\\nCurrent name: ${file_name}`)
                    if (new_name) {
                        const package = new FormData()
                        package.append("path", CurrentFolderPath.value + "/" + file_name)
                        package.append("new_name", new_name)
                        fetch("/actions?type=rename", {method: "POST", body: package}).then(function(response) {
                            if (response.status == 200) {
                                window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value)
                            }
                            else {
                                alert("An unknown error occured")
                            }
                        })
                    }
                }
                else if (event.target.textContent == "Copy") {
                    const package = new FormData()
                    package.append("path", CurrentFolderPath.value + "/" + file_name)
                    fetch("/actions?type=copy_set", {method: "POST", body: package}).then(function(response) {
                        if (response.status == 200) {
                            CopyMoveButton.textContent = "Paste here"
                            CopyMoveButton.style.display = "block"
                            alert("Copied " + file_name + ". Go to the folder where you want to copy this to then click paste")
                        }
                        else {
                            alert("An unknown error occured")
                        }
                    })
                }
                else if (event.target.textContent == "Move") {
                    const package = new FormData()
                    package.append("path", CurrentFolderPath.value + "/" + file_name)
                    fetch("/actions?type=move_set", {method: "POST", body: package}).then(function(response) {
                        if (response.status == 200) {
                            CopyMoveButton.textContent = "Move here"
                            CopyMoveButton.style.display = "block"
                            alert("Copied " + file_name + ". Go to the folder where you want to move this to then click move")
                        }
                        else {
                            alert("An unknown error occured")
                        }
                    })
                }
                else if (event.target.textContent == "Delete") {
                    if (confirm("Do you want to delete " + file_name)) {
                        const package = new FormData()
                        package.append("path", CurrentFolderPath.value + "/" + file_name)
                        fetch("/actions?type=delete", {method: "POST", body: package}).then(function(response) {
                            if (response.status == 200) {
                                window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value)
                            }
                            else {
                                alert("An unknown error occured")
                            }
                        })
                    }
                }
            }
            else if (!(event.target.tagName == "INPUT" && event.target.type == "checkbox")) {
                if (file_icon == "📁") {
                    if (!CurrentFolderPath.value.endsWith("/")) {
                        CurrentFolderPath.value = CurrentFolderPath.value + "/"
                    }
                    window.location.href = "/home?path=" + encodeURIComponent(CurrentFolderPath.value + file_name)
                }
            }
        })
    </script>
</html>"""
                    home_html = home_html.replace("CurrentFolderPathFromPython", current_folder_path)
                    if "source_path" in session:
                        home_html = home_html.replace("DisplayFromPython", "block")
                        if session["source_path"].startswith("Copy"):
                            home_html = home_html.replace("TextFromPython", "Paste here")
                        else:
                            home_html = home_html.replace("TextFromPython", "Move here")
                    else:
                        home_html = home_html.replace("DisplayFromPython", "none")
                    try:
                        folder_contents = os.listdir(current_folder_path)
                    except:
                        error_message = """<div style="display: flex; justify-content: center; align-items: center; height: 485px">
    <div style="background-color: #fee2e2; color: #b91c1c; padding: 20px 30px; border-radius: 8px; font-size: 18px; font-weight: bold; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1)">Error while viewing contents of folder</div>
</div>"""
                        home_html = home_html.replace("FilesFromFolderFromPython", error_message)
                        return home_html
                    if len(folder_contents) == 0:
                        empty_folder_message = """<div style="display: flex; justify-content: center; align-items: center; height: 485px">
<div style="background-color: #f9fafb; color: #374151; padding: 20px 30px; border-radius: 8px; font-size: 18px; font-weight: bold; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1)">Empty folder</div>
</div>"""
                        home_html = home_html.replace("FilesFromFolderFromPython", empty_folder_message)
                        return home_html
                    file_elements = ""
                    folders = []
                    files = []
                    for item in folder_contents:
                        if os.path.isdir(current_folder_path + "/" + item):
                            folders.append(item)
                        else:
                            files.append(item)
                    files = natsorted(files)
                    folders = natsorted(folders)
                    for folder in folders:
                        try:
                            file_elements += f"""<file icon="📁" name="{folder}" last_modified="-" size="-"></file>\n"""
                        except:
                            file_elements += f"""<file icon="❌" name="{folder}" last_modified="-" size="-"></file>\n"""
                    for file in files:
                        file_extension = file.split(".")[-1].lower()
                        if file_extension in ["txt", "pdf", "doc", "py", "js", "html", "java"]:
                            file_icon="📄"
                        elif file_extension in ["png", "jpg", "jpeg", "gif"]:
                            file_icon="📷"
                        elif file_extension in ["exe", "msi"]:
                            file_icon = "⚙️"
                        elif file_extension in ["mp4", "mkv", "avi"]:
                            file_icon="🎬"
                        elif file_extension in ["mp3", "wav", "flac"]:
                            file_icon="🎵"
                        elif file_extension == "lnk":
                            file_icon = "🔗"
                        elif file_extension in ["zip",  "rar",  "7z",  "tar",  "gz"]:
                            file_icon = "🔒"
                        else:
                            file_icon="❓"
                        last_modified = datetime.fromtimestamp(os.path.getmtime(f"{current_folder_path}/{file}")).strftime("%d-%m-%Y %I:%M %p")
                        file_elements += f"""<file icon="{file_icon}" name="{file}" last_modified="{last_modified}" size="{FormattedSize(os.path.getsize(f"{current_folder_path}/{file}"))}"></file>\n"""
                    home_html = home_html.replace("FilesFromFolderFromPython", file_elements)
                    current_folder_path = "/storage/emulated/0"
                    if not os.path.exists(current_folder_path):
                        current_folder_path = str(Path.home()).replace("\\", "/")
                    return home_html
                else:
                    return redirect("/home?path=" + quote(current_folder_path))
    else:
        try:
            if session["logged_in"]:
                path = request.args.get("path")
                for file in request.files.getlist("Files"):
                    os.makedirs(os.path.dirname(f"{path}/{file.filename}"), exist_ok=True)
                    file.save(f"{path}/{file.filename}")
                return ""
            else:
                return "", 300
        except:
            return "", 300
def run_app():
    app.run(host="0.0.0.0", port=5002)
def get_ip():
    socket_instance = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_instance.connect(('8.8.8.8', 8))
    ip =  socket_instance.getsockname()[0]
    socket_instance.close()
    return ip
def start_local_file_sharing(password):
    global website_password, process
    website_password = password
    app.secret_key = os.urandom(24)
    process = Process(target=run_app)
    process.start()
    return "Started Local File Sharing"
def stop_local_file_sharing():
    global process
    process.terminate()
    process = None
    return "Stopped Local File Sharing"
def server_running():
    return process != None