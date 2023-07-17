FROM ubuntu:20.04

USER root

ENV TEMP_WS=/opt \
    WS=/workspace \
    TIMEZONE=Asia/Taipeia

# Setting TimeZone
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get -yq update \
    && apt-get -yq install tzdata \
    && ln -fs /usr/share/zoneinfo/${TIMEZONE} /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata

# Install Basic Package
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get install -yq cmake git libgtk2.0-dev pkg-config yasm libcanberra-gtk-module libcanberra-gtk3-module \
    bsdmainutils zip jq wget \
    openssl libssl-dev openssh-server \
    python3-dev python3-numpy python3-pip \
    tree usbutils lsof vim

# Install Gstreamer
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get install -qy \
	libgstreamer1.0-0 \
	gstreamer1.0-plugins-base \
	gstreamer1.0-plugins-good \
	gstreamer1.0-plugins-bad \
	gstreamer1.0-plugins-ugly \
	gstreamer1.0-libav \
	gstreamer1.0-doc \
	gstreamer1.0-tools \
	libgstreamer1.0-dev \
	libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-rtsp

# Build OpenCV With Gstreamer
WORKDIR $TEMP_WS
RUN git clone --depth=1 -b 4.5.4 https://github.com/opencv/opencv && \
    mkdir -p $TEMP_WS/opencv/build

WORKDIR $TEMP_WS/opencv/build
RUN cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D INSTALL_C_EXAMPLES=OFF \
    -D PYTHON_EXECUTABLE=$(which python3) \
    -D BUILD_opencv_python2=OFF \
    -D CMAKE_INSTALL_PREFIX=$(python3 -c "import sys; print(sys.prefix)") \
    -D PYTHON3_EXECUTABLE=$(which python3) \
    -D PYTHON3_INCLUDE_DIR=$(python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
    -D PYTHON3_PACKAGES_PATH=$(python3 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
    -D WITH_GSTREAMER=ON .. && \
    make -j$(nproc) && \
    make install && \
    ldconfig

# Install Python Package
RUN pip3 install --no-cache-dir \
    wget \
    colorlog \
    gdown==4.5.4 \
    python-dateutil==2.8.2 \
    paho-mqtt==1.6.1 \
    fastapi==0.95.1 \
    "uvicorn[standard]" \
    python-multipart \
    rich

# Install OpenCV input helper
RUN pip3 install --user --no-deps cicv

# Clear Cache
# RUN rm -rf /var/lib/apt/lists/* && \
#     apt-get clean

# Copy Entrypoint
WORKDIR ${WS}
COPY [ "./docker/entrypoint", "/usr/bin/" ]
COPY [ "./", "/workspace/" ]

# Define Entrypoint
ENTRYPOINT [ "/bin/bash", "-l", "-c" ]

# Define Port Number
EXPOSE 1808

# Define CMD
CMD [ "uvicorn main:app --host 0.0.0.0 --port ${PORT}" ]