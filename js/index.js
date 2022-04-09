//drag and drop scripts
let dropArea = document.getElementById('drop-area');
let mask = document.getElementById('icon');

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, preventDefaults, false)
})

function preventDefaults (e) {
  e.preventDefault()
  e.stopPropagation()
};

['dragenter', 'dragover'].forEach(eventName => {
  dropArea.addEventListener(eventName, highlight, false)
});

['dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, unhighlight, false)
});

function highlight() {
  dropArea.classList.add('highlight')
};

function unhighlight() {
  dropArea.classList.remove('highlight')
};

dropArea.addEventListener('drop', handle_drag, false);

function handle_drag(e) {
  let dt = e.dataTransfer
  let file = dt.files[0]
  let filename=file.name.toLowerCase()
  let extension=filename.slice((filename.lastIndexOf(".") - 1 >>> 0) + 2);
  if(extension=="docx"||extension=="pdf"||extension=="jpg"||extension=="jpeg"||extension=="png"){
      handle_file(file)
  }else{
      loading();
      fail();
  }
}

//upload
let labels={
  "0":"First day",
  "1":"Holiday leave",
  "2":"Remuneration",
  "3":"Sick leave",
  "4":"Termination"
}

function handle_file(file){
  resetLoadingSuccess();
  loading();
  hideResult();
  resetContent();
  let obj = new FormData();
  obj.append("file", file);
  //10.0.15.10:8080
  $.ajax({
      url: "http://localhost:5000/yuli/file",
      type: 'POST',
      data: obj,
      contentType: false,
      processData: false,
      mimeType: 'multipart/form-data',
      datatype: 'JSON',
      success: function (data) {
        console.log(data);
        success();        
        setTimeout(
            function (){
              setResult(data);
              showResult();
              resetLoadingSuccess();
            },
            800
        );
      },
      // timeout: 3000,
      error: function () {
        fail();
        setTimeout(
          function (){
            resetLoadingSuccess()
          },
          3000
        );
      }
  })
}

function loading(){
  mask.classList.add('loading')
}

function success(){
  mask.classList.add('success')
}

function fail(){
  mask.classList.add('fail')
}

function resetFail(){
  mask.classList.remove('fail')
}

function resetLoadingSuccess(){
  mask.classList.remove('loading')
  mask.classList.remove('success')
  mask.classList.remove('fail')
}

function showResult(){
  document.getElementById('result').style.cssText="height:auto !important; display:block !important;";
}

function hideResult(){
  document.getElementById('result').style.cssText="";
}

function newElementWithContent(e,c){
  ele=document.createElement(e);
  ele.innerHTML=c;
  return ele;
}

function setResult(data) {
  data = JSON.parse(data);
  let resultDiv=document.getElementById("result");
  if(data["data"].length!=0){

    //create table
    let table=document.createElement("table");
    table.setAttribute('id','resultTable');
    
    //set header
    let tr= document.createElement("tr");
    tr.setAttribute('id','tableHeader');
    tr.appendChild(newElementWithContent('th','Type'));
    tr.appendChild(newElementWithContent('th','Status'));
    tr.appendChild(newElementWithContent('th','Sentence'));    
    table.appendChild(tr);
    
    //add data
    for (i=0;i<data["data"].length;i++){
      let line=JSON.parse(data["data"][i]);
      let tr= document.createElement("tr");
      tr.appendChild(newElementWithContent('td',labels[line["label"]]));
      tr.appendChild(newElementWithContent('td',line["status"]));
      tr.appendChild(newElementWithContent('td',line["data"]));
      table.appendChild(tr);
    }    
    resultDiv.appendChild(table);
  }
}

function resetContent() {
  let target = document.querySelector('#result').getElementsByTagName('table');
  while(target.length!=0){
    target[0].remove();
  }
}