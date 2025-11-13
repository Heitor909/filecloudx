document.addEventListener('DOMContentLoaded',()=>{
  const form=document.getElementById('uploadForm');
  const fileInput=document.getElementById('fileInput');
  const progress=document.getElementById('progress');
  if(!form) return;
  form.addEventListener('submit',e=>{
    e.preventDefault();
    const file=fileInput.files[0];
    if(!file) return alert('Escolha um arquivo');
    const xhr=new XMLHttpRequest();
    const fd=new FormData();
    fd.append('file',file);
    xhr.upload.addEventListener('progress', ev=>{
      if(ev.lengthComputable){
        progress.style.display='block';
        progress.value=Math.round((ev.loaded/ev.total)*100);
      }
    });
    xhr.onload=()=>{ if(xhr.status==200){ alert('Upload completo'); window.location='/' } else { alert('Erro no upload: '+xhr.status) } }
    xhr.open('POST','/upload'); xhr.send(fd);
  });
});