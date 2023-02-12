# Python API For JMComic (禁漫天堂)

封装了一套可用于爬取JM的python api.

简单来说，就是可以通过简单的几行python代码，实现下载JM上的本子集/图片到本地，并且是处理好的图片.

另外，建议使用pip安装模块，使其可以方便地在任意一个地方import.



**友情提示：珍爱JM，为了减轻JM的服务器压力，请不要一次性爬取太多本子，西门🙏🙏🙏**.



## 快速上手

使用下面的两行代码，即可实现功能：把某个本子集（album）里的本子（photo）下载到本地

```python
import jmcomic # 导入此模块，需要先通过pip安装.
jmcomic.download_album('422866') # 传入要下载的album的id，即可下载整个album到本地.
# 上面的这行代码，还有一个可选参数option: JmOption，表示配置项，
# 配置项的作用是告诉程序下载时候的一些选择，
# 比如，要下载到哪个文件夹，使用怎样的路径组织方式（比如[/作者/本子id/图片] 或者 [/作者/本子名称/图片]）.
# 如果没有配置，则会使用 JmOption.default()，下载的路径是[当前工作文件夹/本子名称/图片].
```



进一步的使用可以参考示例代码文件： `/usage/jmcomic_usage.py`，



## 项目特点

- 库依赖很少
- 可配置性强
  - 不配置也能使用，十分方便
  - 配置可以从**配置文件**生成，无需写python代码
  - 配置点有：`是否使用磁盘缓存`  `是否使用代理` `请求元信息 ` `图片下载类型（jpg, png ... ）`等

- 支持debug日志，可开/关/重定向（整体机制较为简单，未使用日志框架）
- 多线程下载
- 跟进了JM最新的图片分割算法（2023-02-08）



##  小小的使用建议

* 本项目只建议开发者了解和使用，因为极简封装的api较少，同时没有文档（^ ^_）。

  想深入高级的使用，自行看源码和改造代码。

* 使用代理访问JM的一些域名会被CloudFlare拦截，无法访问。

  如果一定要使用代理，建议使用配置项`request_meta_data.domain` 指定一个不被CloudFlare拦截的JM域名（当然需要你自己测试哪些域名可用）。

* JM不是前后端分离的网站，因此本api是通过正则表达式解析HTML网页的信息（详见`JmcomicText`），进而实现的下载图片。

  本项目还支持另一种方式，即不解析HTML网页，直接通过路径规律访问直接JM的CDN图床下载本子图片（详见`CdnCrawler`, `FetchStrategy` 等类），不过这种方式的缺点是无法得知本子集的一些信息，如作者信息，本子名称，结果就是下载会到默认文件夹下。



## 项目文件夹介绍

* assets：存放一些非代码的资源文件
  * config：存放配置文件
* modules：存放模块代码
  * jmcomic-core：存放JM核心模块

* test：测试目录，存放测试代码，使用Python自带的unittest
* usage：使用目录，存放使用模块的代码



## 感谢以下项目

### JMComic-qt

   [![Readme Card](https://github-readme-stats.vercel.app/api/pin/?username=tonquer&repo=JMComic-qt)](https://github.com/tonquer/JMComic-qt)

