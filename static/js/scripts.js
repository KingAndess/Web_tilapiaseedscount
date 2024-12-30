function detectImage() {
            const fileInput = document.getElementById('imageUpload');
            const file = fileInput.files[0];
            if (!file) {
                alert("Please select an image file");
                return;
            }

            const formData = new FormData();
            formData.append('image', file);
            fetch('/detect', {
                method: 'POST',
                body: formData
            }).then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('imageResult').innerText = "Error: " + data.error;
                    document.getElementById('uploadedImage').style.display = 'none';
                } else {
                    document.getElementById('imageResult').innerText = "Object Count: " + data.count;
                    document.getElementById('uploadedImage').src = 'data:image/jpeg;base64,' + data.image_data;
                    document.getElementById('uploadedImage').style.display = 'block';
                }
            });
        }

        function detectVideo() {
            const fileInput = document.getElementById('videoUpload');
            const file = fileInput.files[0];
            if (!file) {
                alert("Please select a video file");
                return;
            }

            const formData = new FormData();
            formData.append('video', file);
            fetch('/detect_video', {
                method: 'POST',
                body: formData
            }).then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('videoResult').innerText = "Error: " + data.error;
                    document.getElementById('uploadedVideo').style.display = 'none';
                } else {
                    document.getElementById('videoResult').innerText = "Average Object Count: " + data.average_count;
                    const videoElement = document.getElementById('uploadedVideo');
                    videoElement.src = 'data:video/mp4;base64,' + data.video_data;
                    videoElement.style.display = 'block';
                    videoElement.play();
                }
            });
        }

        function openCameraForPhoto() {
            const cameraInput = document.createElement('input');
            cameraInput.type = 'file';
            cameraInput.accept = 'image/*';
            cameraInput.capture = 'environment';
            cameraInput.onchange = function(event) {
                const file = event.target.files[0];
                if (file) {
                    const formData = new FormData();
                    formData.append('image', file);
                    fetch('/detect', {
                        method: 'POST',
                        body: formData
                    }).then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            document.getElementById('imageResult').innerText = "Error: " + data.error;
                            document.getElementById('cameraPhoto').style.display = 'none';
                        } else {
                            document.getElementById('imageResult').innerText = "Object Count: " + data.count;
                            document.getElementById('cameraPhoto').src = 'data:image/jpeg;base64,' + data.image_data;
                            document.getElementById('cameraPhoto').style.display = 'block';
                        }
                    });
                }
            };
            cameraInput.click();
        }

        function openCameraForVideo() {
            const cameraInput = document.createElement('input');
            cameraInput.type = 'file';
            cameraInput.accept = 'video/*';
            cameraInput.capture = 'environment';
            cameraInput.onchange = function(event) {
                const file = event.target.files[0];
                if (file) {
                    const formData = new FormData();
                    formData.append('video', file);
                    fetch('/detect_video', {
                        method: 'POST',
                        body: formData
                    }).then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            document.getElementById('videoResult').innerText = "Error: " + data.error;
                            document.getElementById('cameraVideo').style.display = 'none';
                        } else {
                            document.getElementById('videoResult').innerText = "Average Object Count: " + data.average_count;
                            const videoElement = document.getElementById('cameraVideo');
                            videoElement.src = 'data:video/mp4;base64,' + data.video_data;
                            videoElement.style.display = 'block';
                            videoElement.play();
                        }
                    });
                }
            };
            cameraInput.click();
        }