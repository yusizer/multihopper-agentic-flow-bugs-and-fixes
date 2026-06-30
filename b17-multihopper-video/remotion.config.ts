import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setCodec("h264");
Config.setConcurrency(2);
Config.setOverwriteOutput(true);
Config.setPixelFormat("yuv420p");
Config.setCrf(18);
