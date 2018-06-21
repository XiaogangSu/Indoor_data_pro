import sys
from osgeo import ogr
from osgeo import gdal
import numpy as np
import os
import xlrd
import shutil
import time

class indoor_map():
    #路径
    path = 'data/'  #总文件路径
    #需要人工输入的变量
    build_name = ''#建筑文件夹名
    bd_id = '' #建筑物id
    m_poi_id = ''  # m_poi_id
    ctime = ''
    mtime = ''

    floor_list = []  #保存楼层文件夹名
    build_category = '' #building类型
    floor_order_dict = {}
    node_dict = {}
    node_list = []
    build_coding = {}
    build_time = {}
    c_name_cate = {}
    en_name = {}
    cate_hei = {}
    node_region_dict = {} #doors与region 对应字典
    nanfei_flid = {} #南非配置表
    mode_select = input('选择建筑物所在区域中国（0）/南非（1）：')

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
        if self.mode_select == '1':
            config_tab = 'config_tab_nanfei.xlsx'
        else:
            config_tab = 'config_tab.xlsx'
        print('读取总配置表：')
        workbook_1 = xlrd.open_workbook('data/' + config_tab)
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
        #self.build_name = 'V2'
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
            if os.path.isdir(path+self.build_name+'/'+line):
                self.floor_list.append(line)
        print(self.floor_list)

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
        # print(self.build_time)

        # nanfei_flid
        if self.mode_select == '1':
            # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            nanfei_flid = {}
            table_6 = workbook_1.sheet_by_name('nanfei_flid')
            nrow6 = table_6.nrows
            # row0 = table_6.row_values(1)
            # nanfei_flid[row0[0]] = {}
            for rownum in range(1, nrow6):
                row = table_6.row_values(rownum)
                key = str(int(row[0]))+'_'+row[1]
                val = row[2]
                self.nanfei_flid[key] = val
            print('nanfei_flid:', self.nanfei_flid)
                # nanfeifl_dict[rownum[1]] = rownum[2]
                # self.nanfei_flid[rownum[0]] = fl

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

        self.build_category = lyr.GetFeature(0)['category']
        print('建筑类型:', self.build_category)
        for feature in lyr:
            feature.SetField('m_poi_id', int(self.m_poi_id))
            feature.SetField('bd_id', int(self.bd_id))
            feature.SetField('c_time', self.ctime)
            feature.SetField('m_time', self.mtime)
            feature.SetField('s_data', 'indoor_navinfo')
            lyr.SetFeature(feature)

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
        print('m_poi fea_num:', fea_num)

        for feature in lyr:
            feature.SetField('m_poi_id', int(self.m_poi_id))
            feature.SetField('category', self.build_category)
            # print('default', feature.GetField('default'))
            if feature.GetField('default') == None:
                feature.SetField('default', 'F1')
            feature.SetField('c_time', self.ctime)
            feature.SetField('m_time', self.mtime)
            lyr.SetFeature(feature)

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
        # print('self.bd_id=', self.bd_id,type(self.bd_id))
        # print('fl_order=', self.floor_order_dict[floor_name][0],type(self.floor_order_dict[floor_name][0]))
        if self.mode_select == '1':
            flid_key = str(int(self.bd_id)) + '_' + floor_name
            fl_id = self.nanfei_flid[flid_key]
        else:
            fl_id = str(int(self.bd_id)) + self.floor_order_dict[floor_name][0]
        # print('fl_id:', fl_id)
        for feature in lyr:
            feature.SetField('fl_id', int(fl_id))
            feature.SetField('fl_name', floor_name)
            feature.SetField('bd_id', int(self.bd_id))
            feature.SetField('c_time', self.ctime)
            feature.SetField('m_time', self.mtime)
            feature.SetField('floornum', int(self.floor_order_dict[floor_name][1]))
            feature.SetField('elevation', 3)

            lyr.SetFeature(feature)

    def base_indoor_region_1(self, floor_name):
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
        for feature in lyr:
            cate = feature.GetField('category')
            c_name = feature.GetField('c_name')
            # print('c_name:', c_name)
            # print('cate:', cate)
            if cate == None:
                if c_name in self.c_name_cate.keys():
                    feature.SetField('category', self.c_name_cate[c_name])
                elif c_name == None:
                    print('c_name字段为空，程序终止！')
                    sys.exit(1)
                elif '楼梯' in c_name:
                    feature.SetField('category', '25134')
                elif '扶梯' in c_name:
                    feature.SetField('category', '25135')
                elif '电梯' in c_name:
                    feature.SetField('category', '25136')
                elif '货梯' in c_name:
                    feature.SetField('category', '25163')

            lyr.SetFeature(feature)

        # for feature in lyr:
        #     cate = feature.GetField('category')
        #     c_name = feature.GetField('c_name')
        #     print('jjjjjjjj')
        #     print(c_name)
        #     # print(c_name)
        #     # print(cate,type(cate))
        #     # if c_name in self.c_name_cate.keys() and cate == None:
        #     #     print('hello...')
        #     #     feature.SetField('category',self.c_name_cate[c_name])
        #     #     if cate in self.cate_hei.keys():
        #     #         feature.SetField('height', self.cate_hei[cate])
        #     if cate in self.cate_hei.keys():
        #         feature.SetField('height', self.cate_hei[cate])
        #
        #     if c_name in self.en_name.keys() and feature.GetField('e_name') == None:
        #         print('hello')
        #         feature.SetField('e_name', self.en_name[c_name])
        #
        #     i = i + 1
        #     order = str(10000 + i)[1:]
        #     value = int(fl_id + order)
        #     feature.SetField('region_id', value)
        #     feature.SetField('fl_id', int(fl_id))
        #     # feature.SetField('heitht', int(self.region_height))
        #     feature.SetField('c_time', self.ctime)
        #     feature.SetField('m_time', self.mtime)
        #
        #     lyr.SetFeature(feature)
        # print('base_indoor_region表处理完成！')

    def base_indoor_region_2(self, floor_name):
        dataname = 'base_indoor_region.shp'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        print('region fea_num:', fea_num)
        if self.mode_select == '1':
            flid_key = str(int(self.bd_id)) + '_' + floor_name
            fl_id = self.nanfei_flid[flid_key]
        else:
            fl_id = str(int(self.bd_id)) + self.floor_order_dict[floor_name][0]
        i = 0
        for feature in lyr:
            cate = feature.GetField('category')
            c_name = feature.GetField('c_name')

            if cate in self.cate_hei.keys():
                feature.SetField('height', self.cate_hei[cate])

            if c_name in self.en_name.keys():
                # print('hello')
                feature.SetField('e_name', self.en_name[c_name])

            i = i + 1
            order = str(10000 + i)[1:]
            value = int(fl_id + order)
            feature.SetField('region_id', value)
            feature.SetField('fl_id', int(fl_id))
            # feature.SetField('heitht', int(self.region_height))
            feature.SetField('c_time', self.ctime)
            feature.SetField('m_time', self.mtime)

            lyr.SetFeature(feature)
        print('base_indoor_region表处理完成！')

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
        if self.mode_select == '1':
            flid_key = str(int(self.bd_id)) + '_' + floor_name
            fl_id = self.nanfei_flid[flid_key]
        else:
            fl_id = str(int(self.bd_id)) + self.floor_order_dict[floor_name][0]
        i = 0
        for feature in lyr:
            i = i + 1
            order = str(10000 + i)[1:]
            value = int(fl_id + order)
            feature.SetField('poi_id', value)
            feature.SetField('fl_id', int(fl_id))
            feature.SetField('c_time', self.ctime)
            feature.SetField('m_time', self.mtime)

            lyr.SetFeature(feature)

    def base_indoor_poi_1(self, floor_name):
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
        for feature in lyr:
            cate = feature.GetField('category')
            c_name = feature.GetField('c_name')
            if cate == None:
                if c_name in self.c_name_cate.keys():
                    feature.SetField('category', self.c_name_cate[c_name])
                elif '楼梯' in c_name:
                    feature.SetField('category', '25134')
                elif '扶梯' in c_name:
                    feature.SetField('category', '25135')
                elif '电梯' in c_name:
                    feature.SetField('category', '25136')
                elif '货梯' in c_name:
                    feature.SetField('category', '25163')
            else:
                continue
            lyr.SetFeature(feature)

    def base_indoor_poi_2(self, floor_name):
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
        if self.mode_select == '1':
            flid_key = str(int(self.bd_id)) + '_' + floor_name
            fl_id = self.nanfei_flid[flid_key]
        else:
            fl_id = str(int(self.bd_id)) + self.floor_order_dict[floor_name][0]
        i = 0
        for feature in lyr:
            c_name = feature.GetField('c_name')

            if c_name in self.en_name.keys():
                # print('hello')
                feature.SetField('e_name', self.en_name[c_name])
            i = i + 1
            order = str(10000 + i)[1:]
            value = int(fl_id + order)
            feature.SetField('poi_id', value)
            feature.SetField('fl_id', int(fl_id))
            feature.SetField('c_time', self.ctime)
            feature.SetField('m_time', self.mtime)

            lyr.SetFeature(feature)

    #base_indoor_node处理
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

        if self.mode_select == '1':
            flid_key = str(int(self.bd_id)) + '_' + floor_name
            fl_id = self.nanfei_flid[flid_key]
        else:
            fl_id = str(int(self.bd_id)) + self.floor_order_dict[floor_name][0]
        i = 0
        for feature in lyr:
            i = i+1
            order = str(10000 + i)[1:]
            value = int(fl_id + order)
            # print('value:', value)
            geo = feature.geometry().GetPoints(0)
            # print(type(a), a)
            feature.SetField('fl_id', fl_id)    #link_id赋值
            feature.SetField('node_id', value)         #kink赋值
            feature.SetField('c_time', self.ctime)         #kink赋值
            feature.SetField('m_time', self.mtime)         #kink赋值
            self.node_list.append(value)
            self.node_dict[value] = geo[0]
            lyr.SetFeature(feature)

        # for i in self.node_list:
        #     print(i)
        #     print(self.node_dict[i])

    def base_indoor_link(self, floor_name):
        dataname = 'base_indoor_link.shp'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + 'fn')
            sys.exit(1)
        lyr = ds.GetLayer(0)
        # defn = lyr.GetLayerDefn()
        # iFieldCount = defn.GetFieldCount()
        # name_list = []   #保存field名称
        #
        # #获取字段定义，GetFieldDefn
        # for i in range(iFieldCount):
        #     oField = defn.GetFieldDefn(i)
        #     name_list.append(oField.GetNameRef())
        #     print('%s: %s(%d.%d)' % (oField.GetNameRef(), oField.GetFieldTypeName(oField.GetType()), oField.GetWidth(), oField.GetPrecision()))

        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        print('indoor_link fea_num:', fea_num)
        # print('geometry:')
        i = 0
        if self.mode_select == '1':
            flid_key = str(int(self.bd_id)) + '_' + floor_name
            fl_id = self.nanfei_flid[flid_key]
        else:
            fl_id = str(int(self.bd_id)) + self.floor_order_dict[floor_name][0]
        for feature in lyr:
            i = i + 1
            # if i == 10:
            #     sys.exit(1)
            order = str(10000 + i)[1:]
            value = int(fl_id + order)
            # print('value:',type(value))
            # print('value:', value)
            geo = feature.geometry().GetPoints(0)
            start_point = geo[0]
            end_point = geo[len(geo) - 1]
            start_dict = {}
            start_dis = []
            end_dict = {}
            end_dis = []
            for j in self.node_list:
                dis_start = pow((start_point[0] - self.node_dict[j][0]), 2) + pow(
                    (start_point[1] - self.node_dict[j][1]), 2)
                start_dict[dis_start] = j
                start_dis.append(dis_start)
                # print(dis_start)
                dis_end = np.sqrt(
                    pow((end_point[0] - self.node_dict[j][0]), 2) + pow((end_point[1] - self.node_dict[j][1]), 2))
                end_dict[dis_end] = j
                end_dis.append(dis_end)
            feature.SetField('source', start_dict[min(start_dis)])
            feature.SetField('target', end_dict[min(end_dis)])
            # print(type(a[0]), a[0])
            feature.SetField('link_id', value)  # link_id赋值

            if feature.GetField('kind') == None:
                print('ddddddfdfdfdfdf')
                feature.SetField('kind', '02')  # 为空时，kind赋值为02
            if feature.GetField('direction') != 1 and feature.GetField('direction') != 2:
                feature.SetField('direction', 0)
            feature.SetField('fl_id', fl_id)
            feature.SetField('c_time', self.ctime)  # kink赋值
            feature.SetField('m_time', self.mtime)
            # feature.SetField('length', feature.geometry().Length())
            # print(feature.geometry().Length())
            lyr.SetFeature(feature)

    def base_indoor_stairs_bak(self, floor_name):
        dataname = 'base_indoor_stairs.dbf'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        fn_bak = self.path + self.build_name + '/' + floor_name + '/'+'base_indoor_stairs_bak.dbf'
        #若备份文件已存在则删除
        if os.path.exists(fn_bak):
            os.remove(fn_bak)
        if os.path.exists(fn):
            os.rename(fn, fn_bak)
            print(dataname+'文件已存在,已修改原文件名为'+'base_indoor_stairs_bak.dbf')
        # 复制base_indoor_node.dbf为'base_indoor_stairs.dbf'
        shutil.copyfile(self.path + self.build_name + '/' + floor_name + '/'+'base_indoor_node.dbf', fn)

        ds = self.driver.Open(fn, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        print('indoor_stairs fea_num:', fea_num)
        lyr.CreateField(ogr.FieldDefn('direction', ogr.OFTString))
        lyr.CreateField(ogr.FieldDefn('to_stairs', ogr.OFTString))
        floor_order = []
        floor_list = self.floor_list
        for i in floor_list:
            floor_order.append(int(self.floor_order_dict[i][0]))
        max_floor = max(floor_order)
        # print(floor_order)

        for feature in lyr:
            # print(type(a), a)
            kind = feature.GetField('kind')
            if kind != '12' and kind != '13' and kind != '14' and kind != '17':
                lyr.DeleteFeature(feature.GetFID())
                continue
            else:
                # print('。。。。。')
                feature.SetField('c_time', self.ctime)
                feature.SetField('m_time', self.mtime)
                kind = feature.GetField('kind')
                temp = str(feature.GetField('node_id'))
                floor = int(temp[5:7])  # 获取楼层代码
                # print('floor=', floor)
                # print()
                if kind == '12' or kind == '13' or kind == '17':
                    # print(floor)
                    if floor == 1:
                        feature.SetField('direction', 2)
                    elif floor == max_floor and floor != 1:
                        feature.SetField('direction', 1)
                    else:
                        feature.SetField('direction', 0)
                lyr.SetFeature(feature)

    def base_indoor_doors_temp(self, floor_name):
        dataname_node = 'base_indoor_node.shp'
        fn_node = os.path.join(self.path, self.build_name,floor_name, dataname_node)
        ds_node = self.driver.Open(fn_node, 1)
        if ds_node is None:
            print('Could not open ' + fn_node + '.shp')
            sys.exit(1)
        lry_node = ds_node.GetLayer(0)
        lry_node.SetAttributeFilter("kind = '16'")   #属性过滤值为16的feature
        # print('门个数：', lry_node.GetFeatureCount())
        # print('过滤后：', lry_node.GetFeatureCount())
        # for feat in lry_node:
        #     print(feat.GetField('kind'))

        #node建立0.3米的buffer
        # buf_memory_driver = ogr.GetDriverByName('Memory')
        # buf_temp_ds = buf_memory_driver.CreateDataSource('temp1')
        # buf_temp_lyr = buf_temp_ds.CreateLayer('buf_lyr')
        # buff_feat = ogr.Feature(buf_temp_lyr.GetLayerDefn())
        # # buf_temp_lyr.CreateFields(lry_node.schema)  #属性表字段定义
        # for node_feat in lry_node:
        #     buff_geom = node_feat.geometry().Buffer(0.3)
        #     tmp = buff_feat.SetGeometry(buff_geom)
        #     tmp = buf_temp_lyr.CreateFeature(buff_feat)

        # dataname_nodebuf = 'node_buf.shp'
        # fn_nodebuf = os.path.join(self.path, self.build_name, floor_name, dataname_nodebuf)
        # ds_nodebuf = self.driver.Open(fn_nodebuf, 1)
        # if ds_node is None:
        #     print('Could not open ' + fn_nodebuf + '.shp')
        #     sys.exit(1)
        # lry_nodebuf = ds_nodebuf.GetLayer(0)
        # lry_nodebuf.SetAttributeFilter("kind = '16'")  # 属性过滤值为16的feature
        # print('要素个数：', lry_nodebuf.GetFeatureCount())

        dataname_region = 'base_indoor_region.shp'
        fn_region = os.path.join(self.path, self.build_name, floor_name, dataname_region)
        ds_region = self.driver.Open(fn_region, 1)
        if ds_region is None:
            print('Could not open ' + fn_region + '.shp')
            sys.exit(1)
        lry_region = ds_region.GetLayer(0)
        # print('region：', lry_region.GetFeatureCount())

        memory_driver = ogr.GetDriverByName('Memory')
        temp_ds = memory_driver.CreateDataSource('temp')
        temp_lyr = temp_ds.CreateLayer('temp')
        lry_region.Intersection(lry_node, temp_lyr)
        # print('相交个数：', temp_lyr.GetFeatureCount())

        node_region_list = []
        node_region_nodeidlist = []
        node_region_dict = {}
        for i in range(temp_lyr.GetFeatureCount()):
            feat = temp_lyr.GetNextFeature()
            # print(feat.GetField('node_id'), feat.GetField('region_id'))
            node_region_list.append([])
            node_region_nodeidlist.append(feat.GetField('node_id'))
            node_region_list[i].append(feat.GetField('node_id'))
            node_region_list[i].append(str(feat.GetField('region_id')))
        nodeid_set = list(set(node_region_nodeidlist))  #set用于删除重复项
        for val in nodeid_set:
            temp_list = []
            for line in node_region_list:
                if line[0] == val:
                    temp_list.append(line[1])
            node_region_dict[val] = '|'.join(temp_list)

        self.node_region_dict = node_region_dict
        # for line in node_region_list:
        #     print(line)

    def base_indoor_stairs(self, floor_name):
        print('开始处理base_indoor_stairs表...')
        dataname = 'base_indoor_stairs.dbf'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        dataname_node = 'base_indoor_node.shp'
        fn_node = self.path + self.build_name + '/' + floor_name + '/' + dataname_node

        ds = self.driver.Open(fn, 1)
        ds_node = self.driver.Open(fn_node, 1)
        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        if ds_node is None:
            print('Could not open ' + fn_node)
            sys.exit(1)
        lyr = ds.GetLayer(0)
        lyr_node = ds_node.GetLayer(0)
        fea_num_node = lyr_node.GetFeatureCount()
        fea_num = lyr.GetFeatureCount()  # 行数，即数据个数
        if fea_num == 0:
            print('base_indoor_stairs 表为空！')
        else:
            for feature in lyr:
                lyr.DeleteFeature(feature.GetFID())
            print('base_indoor_stairs 表已清空！')
        # print('indoor_stairs fea_num:', fea_num)
        # lyr.CreateField(ogr.FieldDefn('direction', ogr.OFTString))
        # lyr.CreateField(ogr.FieldDefn('to_stairs', ogr.OFTString))
        floor_order = []
        floor_list = self.floor_list
        for i in floor_list:
            floor_order.append(int(self.floor_order_dict[i][0]))
        max_floor = max(floor_order)
        # print(floor_order)
        lyr_defn = lyr.GetLayerDefn()
        for feature in lyr_node:
            # print(type(a), a)
            kind = feature.GetField('kind')
            if kind == '12' or kind == '13' or kind == '14' or kind == '17':
                node_id_value = feature.GetField('node_id')
                # print('node_id_value=',node_id_value)
                feat = ogr.Feature(lyr_defn)
                feat.SetField('node_id', node_id_value)
                feat.SetField('c_time', self.ctime)
                # print(self.ctime)
                feat.SetField('m_time', self.mtime)
                temp = str(node_id_value)
                floor = int(temp[5:7])  # 获取楼层代码
                if kind == '12' or kind == '13' or kind == '17':
                # print(floor)
                    if floor == 1 or self.mode_select == '1':
                        feat.SetField('direction', 2)
                    elif floor == max_floor and floor != 1:
                        feat.SetField('direction', 1)
                    else:
                        feat.SetField('direction', 0)
                lyr.CreateFeature(feat)
        print('base_indoor_stairs表处理完成！')

    def base_indoor_doors(self, floor_name):
        print('开始处理base_indoor_doors表...')
        dataname = 'base_indoor_doors.dbf'
        fn = self.path + self.build_name + '/' + floor_name + '/' + dataname
        dataname_node = 'base_indoor_node.shp'
        fn_node = self.path + self.build_name + '/' + floor_name + '/' + dataname_node
        dataname_region = 'base_indoor_node.shp'
        fn_region = self.path + self.build_name + '/' + floor_name + '/' + dataname_region

        ds = self.driver.Open(fn, 1)
        ds_node = self.driver.Open(fn_node, 1)
        ds_region = self.driver.Open(fn_region, 1)

        if ds is None:
            print('Could not open ' + fn)
            sys.exit(1)
        if ds_node is None:
            print('Could not open ' + fn_node)
            sys.exit(1)
        if ds_region is None:
            print('Could not open ' + fn_region)
            sys.exit(1)

        lyr = ds.GetLayer(0)
        lyr_node = ds_node.GetLayer(0)
        lyr_region = ds_region.GetLayer(0)
        # fea_num_node = lyr_node.GetFeatureCount()  # 行数，即数据个数
        fea_num = lyr.GetFeatureCount()
        #若doors表不为空，则清空此表（该操作导致doors不支持人工加批处理的操作方式，若不清空
        # 表，则在后续添加数据时会出错feat = ogr.Feature(lyr_defn)）
        if fea_num == 0:
            print('base_indoor_stairs 表为空！')
        else:
            for feature in lyr:
                lyr.DeleteFeature(feature.GetFID())
            print('base_indoor_stairs 表已清空！')
        lyr_defn = lyr.GetLayerDefn()
        lyr_node.SetAttributeFilter("kind = '16'")
        for feature in lyr_node:
            # print(type(a), a)
            kind = feature.GetField('kind')
            # print('kind=', kind)
            # if kind == '16':
            lyr.DeleteFeature(feature.GetFID())
            node_id_value = feature.GetField('node_id')
            # print('node_id_value=',node_id_value)
            feat = ogr.Feature(lyr_defn)
            feat.SetField('node_id', node_id_value)
            if node_id_value in self.node_region_dict.keys():
                feat.SetField('region_id', self.node_region_dict[node_id_value])
            feat.SetField('c_time', self.ctime)
            # print(self.ctime)
            feat.SetField('m_time', self.mtime)
            feat.SetField('islock', '0')
            feat.SetField('exit', '0')
            feat.SetField('outdoor', '0')
            try:
                feat.SetField('time',self.build_time[self.build_name])
            except:
                print('building_time配置表有误！')
            lyr.CreateFeature(feat)
        print('base_indoor_doors表处理完成！')

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

        if self.mode_select == '1':
            flid_key = str(int(self.bd_id)) + '_' + floor_name
            fl_id = self.nanfei_flid[flid_key]
        else:
            fl_id = str(int(self.bd_id)) + self.floor_order_dict[floor_name][0]
        i = 0
        for feature in lyr:
            i = i + 1
            order = str(10000 + i)[1:]
            value = int(fl_id + order)
            feature.SetField('region_id', value)
            # print(type(a), a)
            feature.SetField('fl_id', fl_id)  # link_id赋值
            feature.SetField('c_time', self.ctime)
            feature.SetField('m_time', self.mtime)
            lyr.SetFeature(feature)

    def base_indoor_sub_region_1(self, floor_name):
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
        if fea_num==0:
            print('base_indoor_sub_region表为空！')
            # sys.exit(1)
        for feature in lyr:
            cate = feature.GetField('category')
            c_name = feature.GetField('c_name')
            if cate == None:
                if c_name in self.c_name_cate.keys():
                    feature.SetField('category', self.c_name_cate[c_name])
                elif '楼梯' in c_name:
                    feature.SetField('category', '25134')
                elif '扶梯' in c_name:
                    feature.SetField('category', '25135')
                elif '电梯' in c_name:
                    feature.SetField('category', '25136')
                elif '货梯' in c_name:
                    feature.SetField('category', '25163')
            else:
                continue
            lyr.SetFeature(feature)

    def base_indoor_sub_region_2(self, floor_name):
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
        if fea_num == 0:
            print('base_indoor_sub_region表为空！')
            # sys.exit(1)
        if self.mode_select == '1':
            flid_key = str(int(self.bd_id)) + '_' + floor_name
            fl_id = self.nanfei_flid[flid_key]
        else:
            fl_id = str(int(self.bd_id)) + self.floor_order_dict[floor_name][0]
        i = 0
        for feature in lyr:
            i = i + 1
            order = str(10000 + i)[1:]
            value = int(fl_id + order)
            feature.SetField('region_id', value)
            # print(type(a), a)
            feature.SetField('fl_id', fl_id)  # link_id赋值
            feature.SetField('c_time', self.ctime)
            feature.SetField('m_time', self.mtime)
            lyr.SetFeature(feature)

    #测试用例，无用
    def region_test(self,floor_name):
        dataname2 = 'base_indoor_sub_region.shp'
        dataname1 = 'base_indoor_region.shp'
        fn1 = self.path + self.build_name + '/' + floor_name + '/' + dataname1
        fn2 = self.path + self.build_name + '/' + floor_name + '/' + dataname2
        # print(fn)
        ds1 = self.driver.Open(fn1, 1)
        if ds1 is None:
            print('Could not open ' + fn1)
            sys.exit(1)
        ds2 = self.driver.Open(fn2, 1)
        if ds2 is None:
            print('Could not open ' + fn2)
            sys.exit(1)
        region_lyr = ds1.GetLayer(0)
        region_feat = region_lyr.GetNextFeature()
        region_geom = region_feat.geometry().Clone()
        subregion_lyr = ds1.GetLayer(0)
        subregion_feat = subregion_lyr.GetNextFeature()
        subregion_geom = subregion_feat.geometry().Clone()
        #数据可是话之后研究后续内容
        for row in subregion_lyr:
            geom = row.geometry()
            ring = geom.GetGeometryRef(0)
            print(ring)
            coords = ring.GetPoints()
            x,y = zip(*coords)
            plt.plot(x, y, 'k')
        plt.axis('equal')
        plt.show()

        print('图形展示')

def main():
    ex = indoor_map()
    ex.map_init()
    ex.base_indoor_city_model()
    ex.base_indoor_m_poi()

    for line in ex.floor_list:
        print('处理楼层：', line)
        ex.base_indoor_fl(line)
        ex.base_indoor_region_1(line)
        ex.base_indoor_region_2(line)
        ex.base_indoor_poi_1(line)
        ex.base_indoor_poi_2(line)
        ex.base_indoor_node(line)
        ex.base_indoor_link(line)
        ex.base_indoor_sub_region_1(line)
        ex.base_indoor_sub_region_2(line)
        ex.base_indoor_stairs(line)
        ex.base_indoor_doors_temp(line)
        ex.base_indoor_doors(line)
    print('处理完成！')

main()