import sys
from osgeo import ogr
from osgeo import gdal
import numpy as np
import os
import xlrd
import shutil
import time


class check():
    # 路径
    path = 'data/'  # 总文件路径
    # 需要人工输入的变量
    build_name = ''  # 建筑文件夹名
    bd_id = ''  # 建筑物id
    m_poi_id = ''  # m_poi_id
    ctime = ''
    mtime = ''

    build_cate_check = {} #建筑物分类表
    floor_list = []  # 保存楼层文件夹名
    build_category = ''  # building类型
    floor_order_dict = {}
    node_dict = {}
    node_list = []
    build_coding = {}
    build_time = {}
    c_name_cate = {}
    en_name = {}
    cate_hei = {}
    node_region_dict = {}  # doors与region 对应字典
    m_poi_id_list1 = []  #m_poi与city_model的mpoi字段一一对应检查
    m_poi_id_list2 = []  #m_poi与city_model的mpoi字段一一对应检查
    city_model_bdid = [] #citymodel 中的build_id
    doors_node_id = [] #doors表nodeid字段
    stairs_node_id = []  # stairs表nodeid字段
    node_node_id = [] #node表nodeid字段
    node_kind = [] #node表kind字段
    region_region_id = []
    floor_floor_id = []

    wrong_list = []

    def map_init(self):
        gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "NO")
        gdal.SetConfigOption("SHAPE_ENCODING", "gb2312")
        # 注册所有的驱动
        ogr.RegisterAll()
        # 数据格式的驱动
        self.driver = ogr.GetDriverByName('ESRI Shapefile')

        self.ctime = time.strftime('%Y%m%d', time.localtime(time.time()))
        # self.ctime = '20180102'
        self.mtime = time.strftime('%Y%m%d', time.localtime(time.time()))
        # self.mtime = '20180102'
        print('读取总配置表：')
        workbook_1 = xlrd.open_workbook('data/config_tab.xlsx')
        table_1 = workbook_1.sheet_by_name('建筑物编码表')
        nrows_1 = table_1.nrows
        for rownum in range(1, nrows_1):
            row = table_1.row_values(rownum)
            # print(type(row),row)
            self.build_coding[row[0]] = []
            self.build_coding[row[0]].append(row[1])  #M_poi_id
            self.build_coding[row[0]].append(row[2])  #bd_id
        print(self.build_coding)
        self.build_name = input('输入建筑名称：')
        # self.build_name = 'V1'
        self.m_poi_id = self.build_coding[self.build_name][0]
        self.bd_id = self.build_coding[self.build_name][1]

        table_2 = workbook_1.sheet_by_name('category及height对照表')
        nrows_2 = table_2.nrows
        # print(nrows_2)
        for rownum in range(1, nrows_2):
            # print('i=',rownum)
            row = table_2.row_values(rownum)
            # print(type(row),row)
            self.cate_hei[str(int(row[0]))] = int(row[1])
        # print(self.cate_hei)
        path = 'data/'
        filelist = os.listdir(path+self.build_name+'/')
        # print(type(filelist))
        for line in filelist:
            # print(line)
            if os.path.isdir(path+self.build_name+'/'+line):  #获取楼层名称（判断是否为文件夹，如果为文件夹，则为楼层）
                self.floor_list.append(line)
        print('楼层名称：', self.floor_list)

        #c_name_cate
        table_3 = workbook_1.sheet_by_name('c_name_cate')
        nrow3 = table_3.nrows
        for rownum in range(1, nrow3):
            # print('i=',rownum)
            row = table_3.row_values(rownum)
            self.c_name_cate[row[0]] = str(int(row[1]))

        #en_name
        table_4 = workbook_1.sheet_by_name('en_name')
        nrow4 = table_4.nrows
        for rownum in range(1, nrow4):
            row = table_4.row_values(rownum)
            self.en_name[row[0]] = row[1]
        # print(self.en_name)

        # building_time
        table_5 = workbook_1.sheet_by_name('building_time')
        nrow5 = table_5.nrows
        for rownum in range(1, nrow5):
            row = table_5.row_values(rownum)
            self.build_time[row[0]] = row[1]
        print(self.build_time)

        # 建筑物分类表
        table_6 = workbook_1.sheet_by_name('building_cate_check')
        nrow6 = table_6.nrows
        for rownum in range(1, nrow6):
            # print(rownum)
            row = table_6.row_values(rownum)
            self.build_cate_check[str(int(row[0]))] = rownum
        # print(self.build_cate_check)

        print('读取建筑配置表：')
        workbook = xlrd.open_workbook(self.path + self.build_name + '/' + 'config.xlsx')
        # print(workbook.sheet_names())
        buildtable1 = workbook.sheet_by_name('floororder')  #文件夹名与楼层序号对应表
        buildnrows1 = buildtable1.nrows
        for rownum in range(1, buildnrows1):
            row = buildtable1.row_values(rownum)
            self.floor_order_dict[row[0]] = []
            self.floor_order_dict[row[0]].append(row[1])
            self.floor_order_dict[row[0]].append(row[2])

    #判断字符串中是否含有中文
    def contain_ch(self, str):
        for ch in str:
            if u'\u4e00' <= ch <= u'\u9fff':
                return (True)
        return (False)

    def base_indoor_city_model(self):
        dataname = 'base_indoor_city_model.shp'
        fn = self.path + self.build_name + '/' + dataname
        # print(fn)
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        print('city_model fea_num:', fea_num)
        #楼层文件夹名称以F开头的数量
        floornum = self.floor_order_dict
        floor = self.floor_list
        F_num = 0
        B_num = 0
        for line in floor:
            # print(line)
            if 'F' in line:
                F_num = F_num+1
            if 'B' in line:
                B_num = B_num-1
        print('B_num=', B_num)
        print('F_num=', F_num)
        str = 'base_indoor_city_model表bd_id:'
        for i in range(fea_num):
            feat = lyr.GetNextFeature()
            bd_id = feat.GetField('bd_id')
            str_temp = str + bd_id
            self.m_poi_id_list1.append(feat.GetField('m_poi_id'))
            self.city_model_bdid.append(feat.GetField('bd_id'))
            # print(feat.GetField('category'))
            # print(type(feat.GetField('up_num')))
            # 检查建筑物分类是否在《建筑物分类表》中，不在则报LOG
            if feat.GetField('category') not in self.build_cate_check.keys():
                self.wrong_list.append(str_temp+ ':'+'category不在建筑物分类表中')
                print('base_indoor_city_model category 不在建筑物分类表中')

            #检查up_num值是否等于楼层文件夹名称以F开头的数量，不等于的，报LOG
            if feat.GetField('up_num') != F_num:
                self.wrong_list.append(str_temp + ':' + 'up_num值错误')
                print('base_indoor_city_model upnum值错误')

            # 检查down_num值是否等于楼层文件夹名称以F（第二次修改为B）开头的数量，不等于的，报LOG
            # print('Bnum=',B_num)
            if feat.GetField('dw_num') != B_num:
                self.wrong_list.append(str_temp + ':' + 'dw_num值错误')
                print('base_indoor_city_model dwnum值错误')

            #检查s_data的值是否为“indoor_navinfo”，不是则报LOG
            if feat.GetField('s_data') != 'indoor_navinfo':
                self.wrong_list.append(str_temp + ':' + 's_data值应为indoor_navinfo')
                print(str_temp + ':' + 's_data值应为"indoor_navinfo"')

            #c_time、m_time格式错误必须为****（年4位）**（月2位）**（日2位），如：20160620，不是则报LOG
            c_time = feat.GetField('c_time')
            m_time = feat.GetField('m_time')
            if c_time is None or m_time is None:
                self.wrong_list.append(str_temp + ':' + 'c_time、m_time值为空')
                print(str_temp + ':' + 'c_time、m_time值为空')
            else:
                if len(c_time) != 8 or len(m_time) != 8:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不对')
                    print('c_time、m_time值不对')

                if c_time != m_time:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不同')
                    print('c_time、m_time值不同')

        del ds

    def base_indoor_m_poi(self):
        dataname = 'base_indoor_m_poi.shp'
        fn = self.path + self.build_name + '/' + dataname
        # print(fn)
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        print('poi fea_num:', fea_num)
        str = 'base_indoor_m_poi表m_poi_id:'
        for i in range(fea_num):
            feat = lyr.GetNextFeature()
            m_poi_id = feat.GetField('m_poi_id')
            str_temp = str + m_poi_id
            self.m_poi_id_list2.append(m_poi_id)
            #检查e_name是否包含中文，包含中文则报LOG
            ename = feat.GetField('e_name')
            if not ename is None and self.contain_ch(ename):
                self.wrong_list.append(str_temp + ':' + 'ename含有中文')
                print(str_temp + ':' + 'ename含有中文')
            # 检查建筑物分类是否在《建筑物分类表》中，不在则报LOG
            if feat.GetField('category') not in self.build_cate_check.keys():
                self.wrong_list.append(str_temp + ':' + 'category不在建筑物分类表中')
                print(str_temp + ':' + 'category不在建筑物分类表中')
            # c_time、m_time格式错误必须为****（年4位）**（月2位）**（日2位），如：20160620，不是则报LOG
            c_time = feat.GetField('c_time')
            m_time = feat.GetField('m_time')
            if c_time is None or m_time is None:
                self.wrong_list.append(str_temp + ':' + 'c_time、m_time值为空')
                print(str_temp + ':' + 'c_time、m_time值为空')
            else:
                if len(c_time) != 8 or len(m_time) != 8:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不对')
                    print('c_time、m_time值不对')

                if c_time != m_time:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不同')
                    print('c_time、m_time值不同')

        del ds

    def base_indoor_fl(self, floor_name):
        dataname = 'base_indoor_fl.shp'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        # print(fn)
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        str = 'base_indoor_fl表'
        for i in range(fea_num):
            feat = lyr.GetNextFeature()
            fl_id = feat.GetField('fl_id')
            self.floor_floor_id.append(fl_id)
            str_temp = floor_name + '层' + str + 'fl_id:'+fl_id
            # c_time、m_time格式错误必须为****（年4位）**（月2位）**（日2位），如：20160620，不是则报LOG
            c_time = feat.GetField('c_time')
            m_time = feat.GetField('m_time')
            if c_time is None or m_time is None:
                self.wrong_list.append(str_temp + ':' + 'c_time、m_time值为空')
                print(str_temp + ':' + 'c_time、m_time值为空')
            else:
                if len(c_time) != 8 or len(m_time) != 8:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不对')
                    print(str_temp + ':' + 'c_time、m_time值不对')

                if c_time != m_time:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不同')
                    print(str_temp + ':' + 'c_time、m_time值不同')
            #fl_name字段必须以F或者B或者M+数字开头，否则报LOG
            fl_name = feat.GetField('fl_name')
            if not fl_name is None and len(fl_name)>1:
                first_L = fl_name[0]
                second_L = fl_name[1]
                if not first_L in ['B','F','M'] or not second_L in ['0','1','2','3','4','5','6','7','8','9']:
                    self.wrong_list.append(str_temp + ':' + 'fl_name字段必须以F或者B或者M+数字开头')
                    print(str_temp + ':' + 'fl_name字段必须以F或者B或者M+数字开头')
            elif not fl_name is None and len(fl_name) <= 1:
                self.wrong_list.append(str_temp + ':' + 'fl_name字段必须以F或者B或者M+数字开头')
                print(str_temp + ':' + 'fl_name字段必须以F或者B或者M+数字开头')
            elif fl_name is None:
                self.wrong_list.append(str_temp + ':' + 'fl_name字段不能为空')
                print(str_temp + ':' + 'fl_name字段不能为空')


            #检查bd_id是否在base_indoor_city_model中存在，不存在报LOG
            if not feat.GetField('bd_id') in self.city_model_bdid:
                self.wrong_list.append(str_temp + ':' + 'bd_id不在在base_indoor_city_model中存在')
                print(str_temp + ':' + 'bd_id不在base_indoor_city_model中存在')
            #检查elevation值是否为3，不为3报LOG
            if feat.GetField('elevation') !=3:
                self.wrong_list.append(str_temp + ':' + 'elevation值不为3')
                print(str_temp + ':' + 'elevation值不为3')

        del ds

    def base_indoor_node_tab(self, floor_name):
        dataname = 'base_indoor_node.shp'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        # print(fn)
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        print('indoor_node fea_num:', fea_num)
        for i in range(fea_num):
            feat = lyr.GetNextFeature()
            node_id = feat.GetField('node_id')
            self.node_node_id.append(node_id)
            # self.node_node_id_kind.append([])
            # self.node_node_id_kind[i].append(feat.GetField('node_id'))
            self.node_kind.append(feat.GetField('kind'))

    def base_indoor_region_tab(self, floor_name):
        dataname = 'base_indoor_region.shp'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        # print(fn)
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        print('indoor_node fea_num:', fea_num)
        for i in range(fea_num):
            feat = lyr.GetNextFeature()
            region_id = feat.GetField('region_id')
            self.region_region_id.append(region_id)
        # print('region_region_id:',self.region_region_id)

    def base_indoor_doors(self, floor_name):
        print('开始处理base_indoor_doors表...')
        dataname = 'base_indoor_doors.dbf'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()
        for i in range(fea_num):
            feat = lyr.GetNextFeature()
            self.doors_node_id.append(feat.GetField('node_id'))
            node_id = feat.GetField('node_id')
            # self.node_node_id.append(node_id)
            str_temp = floor_name + '层' + 'base_indoor_doors表node_id:' + node_id
            #检查node_id是否在base_indoor_node表的node_id中存在，不存在报LOG
            if not feat.GetField('node_id') in self.node_node_id:
                self.wrong_list.append(str_temp + ':' + 'node_id在base_indoor_node表中不存在')
                print(str_temp + ':' + 'node_id在base_indoor_node表中不存在')
            #检查base_indoor_doors表中的node_id对应NODE表中的KIND值是否为16，不是则报LOG
            if node_id in self.node_node_id:
                tempi = self.node_node_id.index(node_id)
                if self.node_kind[tempi] != '16':
                    self.wrong_list.append(str_temp + ':' + 'node_id对应NODE表中的KIND值不为16')
                    print(str_temp + ':' + 'node_id对应NODE表中的KIND值不为16')
            #检查region_id是否在base_indoor_region表中存在，不存在则报LOG，有多条记录时，多条记录都需要检查
            str_tem_cal = feat.GetField('region_id')
            str_cal = []
            if not str_tem_cal is None:
                if len(str_tem_cal)>12:
                    str_cal = str_tem_cal.split('|')
                else:
                    str_cal = [str_tem_cal]
            for line in str_cal:
                if line not in self.region_region_id:
                    # print('region_id:', feat.GetField('region_id'))
                    self.wrong_list.append(str_temp + ':' + 'region_id在base_indoor_region表中不存在')
                    print(str_temp + ':' + 'region_id在base_indoor_region表中不存在')
            #检查exit值是否在｛0，1，2｝范围内，不在则报log
            if not feat.GetField('exit') in ['0','1','2']:
                self.wrong_list.append(str_temp + ':' + 'exit值不在｛0，1，2｝范围内')
                print(str_temp + ':' + 'exit值不在｛0，1，2｝范围内')
            #检查islock值是否在｛0，1｝范围内，不在则报log
            if not feat.GetField('islock') in ['0','1']:
                self.wrong_list.append(str_temp + ':' + 'islock值不在｛0，1｝范围内')
                print(str_temp + ':' + 'islock值不在｛0，1｝范围内')
            #检查outdoor值是否在｛0，1｝范围内，不在则报log
            if not feat.GetField('outdoor') in ['0','1']:
                self.wrong_list.append(str_temp + ':' + 'outdoor值不在｛0，1｝范围内')
                print(str_temp + ':' + 'outdoor值不在｛0，1｝范围内')
            # c_time、m_time格式错误必须为****（年4位）**（月2位）**（日2位），如：20160620，不是则报LOG
            c_time = feat.GetField('c_time')
            m_time = feat.GetField('m_time')
            # print(c_time,m_time)
            if c_time is None or m_time is None:
                self.wrong_list.append(str_temp + ':' + 'c_time、m_time值为空')
                print(str_temp + ':' + 'c_time、m_time值为空')
            else:
                if len(c_time) != 8 or len(m_time) != 8:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不对')
                    print(str_temp + ':' + 'c_time、m_time值不对')
                if c_time != m_time:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不同')
                    print(str_temp + ':' + 'c_time、m_time值不同')

        del ds

    def base_indoor_stairs(self, floor_name):
        print('开始处理base_indoor_stairs表...')
        dataname = 'base_indoor_stairs.dbf'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()
        for i in range(fea_num):
            feat = lyr.GetNextFeature()
            self.stairs_node_id.append(feat.GetField('node_id'))
            node_id = feat.GetField('node_id')
            str_temp = floor_name + '层' + 'base_indoor_stairs表node_id:' + node_id
            #对于stairs表的node_id,如果对应在node表中的kind不为客梯12、货梯13，自动扶梯14，楼梯17四个值，则报log
            if node_id in self.node_node_id:
                tempi = self.node_node_id.index(node_id)
                if not self.node_kind[tempi] in ['12','13','14','17']:
                    self.wrong_list.append(str_temp + ':' + '对应在node表中的kind不为客梯12、货梯13，自动扶梯14，楼梯17四个值')
                    print(str_temp + ':' + '对应在node表中的kind不为客梯12、货梯13，自动扶梯14，楼梯17四个值')
            else:
                #检查node_id是否在base_indoor_node表的node_id中存在，不存在报LOG
                self.wrong_list.append(str_temp + ':' + 'node_id不在base_indoor_node表的node_id中存在')
                print(str_temp + ':' + 'node_id不在base_indoor_node表的node_id中存在')
            #检查direction值是否在｛0，1，2｝范围内，不在则报log
            if not feat.GetField('direction') in [0,1,2,3] and not feat.GetField('direction') is None:
                # print('node_id:',feat.GetField('node_id'),'dirention:', feat.GetField('direction'))
                self.wrong_list.append(str_temp + ':' + 'direction值不在｛0，1，2, 3｝范围内')
                print(str_temp + ':' + 'direction值不在｛0，1，2，3｝范围内')
            # c_time、m_time格式错误必须为****（年4位）**（月2位）**（日2位），如：20160620，不是则报LOG
            c_time = feat.GetField('c_time')
            m_time = feat.GetField('m_time')
            # print(c_time,m_time)
            if c_time is None or m_time is None:
                self.wrong_list.append(str_temp + ':' + 'c_time、m_time值为空')
                print(str_temp + ':' + 'c_time、m_time值为空')
            else:
                if len(c_time) != 8 or len(m_time) != 8:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不对')
                    print(str_temp + ':' + 'c_time、m_time值不对')
                if c_time != m_time:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不同')
                    print(str_temp + ':' + 'c_time、m_time值不同')

        del ds

    def base_indoor_node(self, floor_name):
        dataname = 'base_indoor_node.shp'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        # print(fn)
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        # self.node_num = fea_num  #获取node要素个数，并赋给全局变量
        print('indoor_node fea_num:', fea_num)
        # str = 'base_indoor_node表'
        for i in range(fea_num):
            feat = lyr.GetNextFeature()
            node_id = feat.GetField('node_id')
            # self.node_node_id.append(node_id)
            str_temp = floor_name + '层' + 'base_indoor_node表node_id:' + node_id
            # c_time、m_time格式错误必须为****（年4位）**（月2位）**（日2位），如：20160620，不是则报LOG
            c_time = feat.GetField('c_time')
            m_time = feat.GetField('m_time')
            # print(c_time,m_time)
            if c_time is None or m_time is None:
                self.wrong_list.append(str_temp + ':' + 'c_time、m_time值为空')
                print(str_temp + ':' + 'c_time、m_time值为空')
            else:
                if len(c_time) != 8 or len(m_time) != 8:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不对')
                    print(str_temp + ':' + 'c_time、m_time值不对')
                if c_time != m_time:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不同')
                    print(str_temp + ':' + 'c_time、m_time值不同')
            #检查kind值是否在｛10,12,13，14，15，16，17｝范围内，不在则报log
            if not feat.GetField('kind') in ['10','12','13','14','15','16','17']:
                self.wrong_list.append(str_temp + ':' + 'kind不在值域内')
                print(str_temp + ':' + 'kind不在值域内')
            #检查NODE表中KIND值为16的node_id是否都在 base_indoor_doors表中，不在则报LOG
            if feat.GetField('kind') == '16' and not feat.GetField('node_id') in self.doors_node_id:
                self.wrong_list.append(str_temp + ':' + 'kind为16时，node_id不在doors表内')
                print(str_temp + ':' + 'kind为16时，node_id不在doors表内')
            #对于node表的node如果kind为客梯12，货梯13，自动扶梯14，楼梯17四个值，在stairs表里必须能查到该node点，否则，报log
            # print(self.stairs_node_id)
            if feat.GetField('kind') in ['12','13','14','17'] and not feat.GetField('node_id') in self.stairs_node_id:
                self.wrong_list.append(str_temp + ':' + 'kind为12、13、14、17时，node_id不在stairs表内')
                print(str_temp + ':' + 'kind为12、13、14、17时，node_id不在stairs表内')
            if not feat.GetField('fl_id') in self.floor_floor_id:
                self.wrong_list.append(str_temp + ':' + 'fl_id在base_indoor_fl表中不存在')
                print(str_temp + ':' + 'fl_id在base_indoor_fl表中不存在')

        del ds

    def base_indoor_link(self, floor_name):
        dataname = 'base_indoor_link.shp'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + 'fn')
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        print('indoor_link fea_num:', fea_num)
        for i in range(fea_num):
            feat = lyr.GetNextFeature()
            link_id = feat.GetField('link_id')
            str_temp = floor_name + '层' + 'base_indoor_link表link_id:' + link_id
            # c_time、m_time格式错误必须为****（年4位）**（月2位）**（日2位），如：20160620，不是则报LOG
            c_time = feat.GetField('c_time')
            m_time = feat.GetField('m_time')
            if c_time is None or m_time is None:
                self.wrong_list.append(str_temp + ':' + 'c_time、m_time值为空')
                print(str_temp + ':' + 'c_time、m_time值为空')
            else:
                if len(c_time) != 8 or len(m_time) != 8:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不对')
                    print(str_temp + ':' + 'c_time、m_time值不对')
                if c_time != m_time:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不同')
                    print(str_temp + ':' + 'c_time、m_time值不同')

            #检查KIND值是否在《LINK的KIND值域表》表中存在，不存在报LOG
            kind = feat.GetField('kind')
            if not kind in ['01','02','03','04','05','06','07','08']:
                self.wrong_list.append(str_temp + ':' + 'KIND值在《LINK的KIND值域表》表中不存在')
                print(str_temp + ':' + 'KIND值在《LINK的KIND值域表》表中不存在')
            #检查source值是否在base_indoor_node表的node_id中存在，不存在报LOG
            if not feat.GetField('source') in self.node_node_id:
                self.wrong_list.append(str_temp + ':' + 'source不在node_id中')
                print(str_temp + ':' + 'source不在node_id中')
            #检查target值是否在base_indoor_node表的node_id中存在，不存在报LOG
            if not feat.GetField('target') in self.node_node_id:
                self.wrong_list.append(str_temp + ':' + 'target不在node_id中')
                print(str_temp + ':' + 'target不在node_id中')
            #检查direction值是否在｛0,1,2｝范围内，不在则报log
            if not feat.GetField('direction') in [0, 1, 2]:
                self.wrong_list.append(str_temp + ':' + 'direction值不在｛0,1,2｝范围内')
                print(str_temp + ':' + 'direction值不在｛0,1,2｝范围内')
            #检查length值小数点后位数是否大于3，大于3报LOG
            length = feat.GetField('length')
            length_str = str(length).split('.')
            if len(length_str[1]) >3:
                self.wrong_list.append(str_temp + ':' + 'length值小数点后位数是大于3')
                print(str_temp + ':' + 'length值小数点后位数是大于3')
            if not feat.GetField('fl_id') in self.floor_floor_id:
                self.wrong_list.append(str_temp + ':' + 'fl_id在base_indoor_fl表中不存在')
                print(str_temp + ':' + 'fl_id在base_indoor_fl表中不存在')

        del ds

    # def dict_sort(self,dict): #按照字典的value排顺序，在poi与region表中用到
    #     key_list = list(dict.keys())
    #     dict_templist = []
    #     for i in range(len(key_list)):
    #         dict_templist.append([i,key_list[i],dict[key_list[i]][0],dict[key_list[i]][1]])
    #
    #     for val in key_list:
    #         dict_temp[dict[val][0] + val] = val
    #
    #
    #     keys_sort = list(dict_temp.keys())
    #     keys_sort.sort()
    #     dict_final = {}
    #     for key_sort in keys_sort:
    #         dict_final[dict_temp[key_sort]] = dict[dict_temp[key_sort]]
    #     return(dict_final)
    #

    def base_indoor_poi(self, floor_name):
        dataname = 'base_indoor_poi.shp'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        # print(fn)
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        print('poi fea_num:', fea_num)
        cname_cate = []
        # cname = []
        for i in range(fea_num):
            feat = lyr.GetNextFeature()
            poi_id = feat.GetField('poi_id')
            str_temp = floor_name + '层' + 'base_indoor_poi表poi_id:' + poi_id
            cname_cate.append([])
            cname_cate[i].append(feat.GetField('c_name'))
            cname_cate[i].append(feat.GetField('category'))
            cname_cate[i].append(feat.GetField('poi_id'))
            #检查poi表里的category为101824（第二次修改为91033）和25056的poi，sub_kind必须有值,如果无值，报log
            if feat.GetField('category') in ['91033', '25056', '25055'] and feat.GetField('sub_kind') is None:
                self.wrong_list.append(str_temp + ':' + 'poi表里的category为91033、25056、25055的sub_kind必须有值')
                print(str_temp + ':' + 'poi表里的category为91033、25056、25055的sub_kind必须有值')
            # c_time、m_time格式错误必须为****（年4位）**（月2位）**（日2位），如：20160620，不是则报LOG
            c_time = feat.GetField('c_time')
            m_time = feat.GetField('m_time')
            if c_time is None or m_time is None:
                self.wrong_list.append(str_temp + ':' + 'c_time、m_time值为空')
                print(str_temp + ':' + 'c_time、m_time值为空')
            else:
                if len(c_time) != 8 or len(m_time) != 8:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不对')
                    print(str_temp + ':' + 'c_time、m_time值不对')
                if c_time != m_time:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不同')
                    print(str_temp + ':' + 'c_time、m_time值不同')
            # 检查e_name是否包含中文，包含中文则报LOG
            ename = feat.GetField('e_name')
            if not ename is None and self.contain_ch(ename):
                self.wrong_list.append(str_temp + ':' + 'ename含有中文')
                print(str_temp + ':' + 'ename含有中文')
            if not feat.GetField('fl_id') in self.floor_floor_id:
                self.wrong_list.append(str_temp + ':' + 'fl_id在base_indoor_fl表中不存在')
                print(str_temp + ':' + 'fl_id在base_indoor_fl表中不存在')

        #计算POI表中，poi名称（c_name）如果相同，但是分类(category)不相同。报log,
        cname_cate_bak = cname_cate
        dif_name_category = [] #保存初次循环获取的name相同，类型不同的数据
        dif_name_category_dict = {} #最终获取的name相同，类型不同的数据
        for line in cname_cate:
            for line2 in cname_cate_bak:
                if line[0] == line2[0] and line[1] != line2[1]:
                    dif_name_category.append(line)
        dif_name_category_sort = {}
        if len(dif_name_category) != 0:
            for val in dif_name_category:
                dif_name_category_dict[val[2]] = [val[0],val[1]]
            self.wrong_list.append(floor_name + '层' + 'base_indoor_poi表poi_id:'+ 'poi名称（c_name）相同，但是分类(category)不相同:')
            keys_list = list(dif_name_category_dict.keys())
            keys_list.sort()
            # dif_name_category_dict_sort=self.dict_sort(dif_name_category_dict)
            dif_name_category_sort = dif_name_category_dict
            # print(dif_name_category_dict_sort)
            for key in dif_name_category_sort.keys():
                self.wrong_list.append('==== '+str(key)+','+dif_name_category_sort[key][0]+','+ dif_name_category_sort[key][1])
        print(floor_name + '层' + 'base_indoor_poi表poi_id:'+ 'poi名称（c_name）相同，但是分类(category)不相同:', dif_name_category_sort)
        del ds

    def base_indoor_region(self, floor_name):
        dataname = 'base_indoor_region.shp'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()  #行数，即数据个数
        print('region fea_num:', fea_num)
        # fl_id = str(int(self.bd_id)) + self.floor_order_dict[floor_name][0]
        # i = 0
        cname_cate = []
        for i in range(fea_num):
            feat = lyr.GetNextFeature()
            region_id = feat.GetField('region_id')
            cname_cate.append([])
            cname_cate[i].append(feat.GetField('c_name'))
            cname_cate[i].append(feat.GetField('category'))
            cname_cate[i].append(feat.GetField('region_id'))
            str_temp = floor_name + '层' + 'base_indoor_region表region_id:' + region_id
            # c_time、m_time格式错误必须为****（年4位）**（月2位）**（日2位），如：20160620，不是则报LOG
            c_time = feat.GetField('c_time')
            m_time = feat.GetField('m_time')
            if c_time is None or m_time is None:
                self.wrong_list.append(str_temp + ':' + 'c_time、m_time值为空')
                print(str_temp + ':' + 'c_time、m_time值为空')
            else:
                if len(c_time) != 8 or len(m_time) != 8:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不对')
                    print(str_temp + ':' + 'c_time、m_time值不对')
                if c_time != m_time:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不同')
                    print(str_temp + ':' + 'c_time、m_time值不同')
            # 检查e_name是否包含中文，包含中文则报LOG
            ename = feat.GetField('e_name')
            if not ename is None and self.contain_ch(ename):
                self.wrong_list.append(str_temp + ':' + 'ename含有中文')
                print(str_temp + ':' + 'ename含有中文')
            if not feat.GetField('fl_id') in self.floor_floor_id:
                self.wrong_list.append(str_temp + ':' + 'fl_id在base_indoor_fl表中不存在')
                print(str_temp + ':' + 'fl_id在base_indoor_fl表中不存在')

        # 计算region表中，region名称（c_name）如果相同，但是分类(category)不相同。报log
        cname_cate_bak = cname_cate
        dif_name_category = []  # 保存初次循环获取的name相同，类型不同的数据
        dif_name_category_dict = {}  # 最终获取的name相同，类型不同的数据
        for line in cname_cate:
            for line2 in cname_cate_bak:
                if line[0] == line2[0] and line[1] != line2[1]:
                    dif_name_category.append(line)
                    # self.wrong_list.append(floor_name + '层' + 'base_indoor_region表region_id:' + line[2] + 'poi名称（c_name）相同，但是分类(category)不相同')
                    # print(floor_name + '层' + 'base_indoor_region表region_id:' + line[2] + 'region名称（c_name）相同，但是分类(category)不相同')
        if len(dif_name_category) != 0:
            for val in dif_name_category:
                dif_name_category_dict[val[2]] = [val[0],val[1]]
            self.wrong_list.append(floor_name + '层' + 'base_indoor_poi表poi_id:'+ 'poi名称（c_name）相同，但是分类(category)不相同:')
            for key in dif_name_category_dict.keys():
                self.wrong_list.append('==== '+str(key)+','+dif_name_category_dict[key][0]+','+dif_name_category_dict[key][1])
        print(floor_name + '层' + 'base_indoor_poi表poi_id:'+ 'poi名称（c_name）相同，但是分类(category)不相同:',dif_name_category_dict)

        del ds

    def base_indoor_sub_region(self, floor_name):
        dataname = 'base_indoor_sub_region.shp'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        # print(fn)
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        print('indoor_sub_region fea_num:', fea_num)
        for i in range(fea_num):
            feat = lyr.GetNextFeature()
            region_id = feat.GetField('region_id')
            str_temp = floor_name + '层' + 'base_indoor_sub_region表region_id:' + region_id
            # c_time、m_time格式错误必须为****（年4位）**（月2位）**（日2位），如：20160620，不是则报LOG
            c_time = feat.GetField('c_time')
            m_time = feat.GetField('m_time')
            if c_time is None or m_time is None:
                self.wrong_list.append(str_temp + ':' + 'c_time、m_time值为空')
                print(str_temp + ':' + 'c_time、m_time值为空')
            else:
                if len(c_time) != 8 or len(m_time) != 8:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不对')
                    print(str_temp + ':' + 'c_time、m_time值不对')
                if c_time != m_time:
                    self.wrong_list.append(str_temp + ':' + 'c_time、m_time值不同')
                    print(str_temp + ':' + 'c_time、m_time值不同')

            if not feat.GetField('fl_id') in self.floor_floor_id:
                self.wrong_list.append(str_temp + ':' + 'fl_id在base_indoor_fl表中不存在')
                print(str_temp + ':' + 'fl_id在base_indoor_fl表中不存在')

    #检查m_poi_id是否与base_indoor_city_model表的m_poi_id一一对应，不是则报LOG
    def mpoi_city(self):
        for line in self.m_poi_id_list1:
            for line2 in self.m_poi_id_list2:
                if line != line2:
                    self.wrong_list.append('m_poi_id是否与base_indoor_city_model表的m_poi_id无法一一对应')
                    print('m_poi_id与base_indoor_city_model表的m_poi_id无法一一对应')
        for line in self.m_poi_id_list2:
            for line2 in self.m_poi_id_list1:
                if line != line2:
                    self.wrong_list.append('m_poi_id是否与base_indoor_city_model表的m_poi_id无法一一对应')
                    print('m_poi_id与base_indoor_city_model表的m_poi_id无法一一对应')

    def save_wrong(self):
        savename = 'wrong.txt'
        path = os.path.join(self.path,self.build_name,savename)
        with open(path, 'w') as file:
            for line in self.wrong_list:
                file.write(line)
                file.write('\n')


def main():
    ex = check()
    ex.map_init()
    ex.base_indoor_city_model()
    ex.base_indoor_m_poi()
    ex.mpoi_city()
    for line in ex.floor_list:
        print('处理楼层：', line)
        ex.base_indoor_fl(line)
        ex.base_indoor_node_tab(line)
        ex.base_indoor_region_tab(line)
        ex.base_indoor_doors(line)
        ex.base_indoor_stairs(line)
        ex.base_indoor_node(line)
        ex.base_indoor_link(line)
        ex.base_indoor_poi(line)
        ex.base_indoor_region(line)

    ex.save_wrong()

main()