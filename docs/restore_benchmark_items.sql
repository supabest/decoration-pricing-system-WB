-- 恢复 benchmark_items（497 条，来源：基准价2025.xlsx）
-- 在 Supabase Dashboard → SQL Editor 粘贴执行

BEGIN;
-- 如需先清空旧数据，取消下一行注释：
-- DELETE FROM benchmark_items;

INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-01', '泥水工', '地面-水泥砂浆找平', '1.工作内容：包含完成地面找平所需的场地清理、打灰饼、水泥砂浆搅拌、素水泥浆纵横各扫一道（内掺建筑胶）、材料运输、找平抹灰压光、超高降效等费用等一切工作；
2.材料种类：水泥砂浆（WS）
3.材料厚度:50mm
4.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）
5.综合考虑:基层清理、抹面压光、超高降效等费用；', 'm2', 20.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-02', '泥水工', '地面-楼梯面水泥砂浆找平层', '1.工作内容：包含完成地面找平所需的场地清理、打灰饼、水泥砂浆搅拌、素水泥浆纵横各扫一道（内掺建筑胶）、材料运输、找平抹灰压光、超高降效等费用等一切工作；
2.材料种类：水泥砂浆（WS）
3.材料厚度:50mm
4.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）
5.综合考虑:基层清理、抹面压光、超高降效等费用；', 'm2', 24.0, '按展开面积计算');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-03', '泥水工', '地面-细石混凝土混凝土找平层', '1.工作内容：包含完成地面细石混凝土回填层所需场地清理、标高定位、细石混凝土搅拌、材料运输等一切工作；
2.材料种类：细石混凝土
3.材料厚度:50mm
4.综合考虑:基层清理、抹面压光、擦缝及净面、超高降效等费用', 'm2', 20.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-04', '泥水工', '地面-陶粒混凝土回填', '1.工作内容：包含完成陶粒混凝土回填层所需的场地清理、标高定位、陶粒混凝土搅拌、材料运输等一切工作；      
2.材料种类:疏水陶粒
3.综合考虑:基层处理、回填及平整、超高降效等增加费', 'm3', 75.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-05', '泥水工', '地面-沉箱砌砖架空层', '1.工作内容：包含完成沉箱砌砖架空层所需的场地清理、标高定位、材料运输等一切工作；      
2.砌块种类、强度等级:灰砂砖
3.砂浆强度等级:砌筑砂浆
4.综合考虑:砌筑厚度、砌筑类型、超高降效等费用', 'm3', 280.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-06', '泥水工', '地面-沉箱预制盖板安装', '1.工作内容：包含完成沉箱预制盖板所需的场地清理、标高定位、材料运输等一切工作； 
2.盖板厚度:60mm；
3.钢筋品种、强度等级：Φ6mm@150mm（双层双向）；
4.综合考虑:预制盖板制安、钢筋网绑扎、模板制安、抹灰、二次搬运、超高降效等费用；', 'm2', 75.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-07', '泥水工', '地面-水泥自流平漆', '1.工作内容：包含完成地面找平所需的场地清理、打灰饼、水泥自流平漆搅拌、材料运输、找平抹灰压光等一切工作；
2.面层材料规格、品种:3mm厚水泥自流平漆
3.基层处理:专用界面剂
4.综合考虑:基层打磨、分层涂刷、镘刀刮面、超高降效等费用', 'm2', 13.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-08', '泥水工', '地面铺设-瓷砖地面铺贴', '1.工作内容：包含地面地砖施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、开孔、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.材料规格：最长边1500mm以（含）内；
4.嵌缝材料种类:专用勾缝剂填缝；
5.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 50.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-09', '泥水工', '地面铺设-瓷砖地面铺贴', '1.工作内容：包含地面地砖施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、开孔、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.材料规格：最长边1500mm以外(大板砖）；
4.嵌缝材料种类:专用勾缝剂填缝；
5.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 80.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-010', '泥水工', '地面铺设-瓷砖地面斜铺、点缀、拼花、零星地砖', '1.工作内容：包含地面地砖施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、开孔、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.材料规格：按图纸要求；
4.嵌缝材料种类:专用勾缝剂填缝；
5.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 60.0, '按展开面积计算');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-011', '泥水工', '地面铺设-瓷砖楼梯面铺贴', '1.工作内容：包含地面地砖施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、开孔、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.材料规格：按图纸要求；
4.嵌缝材料种类:专用勾缝剂填缝；
5.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 60.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-012', '泥水工', '地面铺设-门槛/波打线瓷砖铺贴', '1.工作内容：包含地面地砖施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、开孔、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.材料规格：按图纸要求；
4.嵌缝材料种类:专用勾缝剂填缝；
5.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 60.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-013', '泥水工', '地面铺设-瓷砖零星铺贴', '1.工作内容：包含地面地砖施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、开孔、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.材料规格：按图纸要求；
4.嵌缝材料种类:专用勾缝剂填缝；
5.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 80.01, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-014', '泥水工', '地面铺设-马赛克', '1.工作内容：包含地面马赛克铺设所需的场地清理，放线定位、材料运输、必要的现场切割加工、安装、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.材料规格：按图纸要求；
4.嵌缝材料种类:专用勾缝剂填缝；
5.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 57.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-015', '泥水工', '地面铺设-石材', '1.工作内容：包含地面石材施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、开孔、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（符合设计要求）；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 80.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-016', '泥水工', '地面铺设-石材拼花', '1.工作内容：包含地面石材施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、开孔、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（符合设计要求）；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 96.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-017', '泥水工', '地面铺设-石材门槛/波打线', '1.工作内容：包含地面石材施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、开孔、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（符合设计要求）；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 96.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-018', '泥水工', '地面铺设-零星石材', '1.工作内容：包含地面石材施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、开孔、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（符合设计要求）；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 115.2, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-019', '泥水工', '地面铺设-石材楼梯', '1.工作内容：包含地面石材施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、开孔、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（符合设计要求）；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 96.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-020', '泥水工', '地面-石材档水石铺贴', '1.工作内容：包含地面石材线条施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.材料规格：石线宽度100mm以内；
4.嵌缝材料种类:专用勾缝剂填缝；
5.基层处理:素水泥浆纵横各扫一道（符合设计要求）；
6.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
7.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm', 17.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-021', '泥水工', '石材脚座制安', '1.工作内容：包含地面石材线条施工所需的场地清理、放线定位、材料运输、干拌水泥砂浆、结合层、必要的现场切割加工、铺设、填缝等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（符合设计要求）；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', '组', 40.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-022', '泥水工', '石材磨边', '1.工作内容：包括完成石材磨边所需的一切工作；
2.磨边类型:法国边、海棠边等复杂造型；
3.综合考虑:磨边尺寸、磨边方式、超高降效等费用；', 'm', 8.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-023', '泥水工', '石材磨边', '1.工作内容：包括完成石材磨边所需的一切工作；
2.磨边类型:斜边、圆边等简易造型；
3.综合考虑:磨边尺寸、磨边方式、超高降效等费用；', 'm', 6.85, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-024', '泥水工', '石材开槽', '1.工作内容：包括完成石材开槽所需的一切工作；
2.磨边类型:凹凸槽；
3.综合考虑:拉槽尺寸、拉槽方式、超高降效等费用；', 'm', 6.13, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-025', '泥水工', '地面-地梁', '1.工作内容：包含完成地面地梁所需的材料运输、模板、钢筋制作安装、混凝土捣制、脱模等一切工作；
2.其他：截面面积0.06m2以内；0.06m2以外地梁人工费按照1.1系数计算；', 'm', 48.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-026', '泥水工', '楼地面-变形缝', '1.工作内容：包含完成变形缝所需的后浇带部分做止水钢板等一切工作；
2.其他：墙面变形缝参照地面变形缝；', 'm', 20.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-027', '泥水工', '踢脚线打凿', '1.工作内容：打凿墙身水泥砂浆基层，踢脚线嵌入墙内、与墙面平齐；
2.综合考虑:打凿方式、打凿宽度、超高降效等费用；', 'm', 6.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-028', '泥水工', '墙面基层-水泥砂浆', '1.工作内容：包含完成地面找平所需的场地清理、打灰饼、水泥砂浆搅拌、素水泥浆纵横各扫一道（内掺建筑胶）、材料运输、找平抹灰压光、超高降效等费用等一切工作；
2.水泥砂浆厚度：20mm以内；配合比需满足施工要求；
3.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）；
4.综合考虑:基层类型、抹面压光、超高降效等费用；', 'm2', 20.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-029', '泥水工', '墙面基层-墙面瓷砖背胶处理', '1.工作内容：完成墙面界面剂所需材料运输、搅拌、墙面找平等一切工作；
2.材料种类:专用瓷砖背胶；
3.综合考虑:背胶厚度、瓷砖清洁、涂刷背胶、干燥等费用；', 'm2', 7.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-030', '泥水工', '墙面隔墙-墙体砌筑', '1.工作内容：完成墙面砌砖墙体植拉结筋、运砖、砖洇水、搅拌砂浆、运输砂浆、砌砖墙、墙面养护等一切工作内容；
2.砌块种类、强度等级:灰砂砖；
3.砌块规格尺寸:各种厚度；
4.砂浆强度等级:专用砌筑砂浆；
5.综合考虑:墙体厚度、墙体类型、超高降效等费用；', 'm3', 304.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-031', '泥水工', '墙面隔墙-零星砌体', '1.工作内容：完成墙面砌砖墙体植拉结筋、运砖、砖洇水、搅拌砂浆、运输砂浆、砌砖墙、墙面养护等一切工作内容；
2.砌块种类、强度等级:灰砂砖；
3.砌块规格尺寸:各种厚度；
4.砂浆强度等级:专用砌筑砂浆；
5.综合考虑:墙体厚度、墙体类型、超高降效等费用；', 'm3', 396.18, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-032', '泥水工', '墙面隔墙-圈梁、构造柱、地梁', '1.工作内容：完成墙面圈梁、构造柱墙体放线定位、植拉结筋、绑扎构造柱钢筋、支构造柱模板、浇筑、构造柱混凝土、拆模、墙面养护等一切工作内容；
2.规格：300mm以内；
3.综合考虑:墙体厚度、圈梁、构造柱、地梁类型、超高降效等费用；', 'm3', 280.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-033', '泥水工', '墙面-钢丝网加固', '1.工作内容：完成墙面钢丝网加工所需材料运输、必要的钢丝网现场切割、安装固定墙体抗裂钢丝网片等一切工作工作；
2.加固方式：不同材料相交位置贴300宽钢丝网片；', 'm2', 9.2, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-034', '泥水工', '墙面饰面-墙柱面瓷砖粘贴', '1.工作内容：完成墙面墙砖所需的材料运输、基层处理、砖洇水、背胶、必要的墙砖现场切割、结合层搅拌、开孔、墙面砖黏贴等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（加建筑胶）或专用固化剂；
5.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 50.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-035', '泥水工', '墙面饰面-墙柱面瓷砖挂贴', '1.工作内容：完成墙面墙砖所需的材料运输、基层处理、砖洇水、背胶、必要的墙砖现场切割、结合层搅拌、开孔、墙面砖黏贴等一切工作；
2.挂件材质品种:水泥钢射钉/螺栓、铜丝及镀铜扣片等；
3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（加建筑胶）或专用固化剂；
5.综合考虑:按图铺贴、切割开孔、钻孔成槽、安装膨胀螺栓、防护材料、防空鼓措施、超高降效、配合材料下单等费用；', 'm2', 70.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-036', '泥水工', '墙面饰面-墙柱面瓷砖干挂', '1.工作内容：完成墙面墙砖所需的材料运输、基层处理、砖洇水、背胶、必要的墙砖现场切割、结合层搅拌、开孔、墙面砖黏贴等一切工作；
2.挂件材质品种:不锈钢挂件，符合设计及规范要求；
3.龙骨材质品种:国标镀锌型材骨架，符合设计及规范要求；
4.嵌缝材料种类:专用勾缝剂填缝；
5.基层处理:素水泥浆纵横各扫一道（加建筑胶）或专用固化剂；
6.综合考虑:按图铺贴、切割开孔、钻孔成槽、安装膨胀螺栓、超高降效、配合材料下单等费用；', 'm2', 90.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-037', '泥水工', '墙面饰面-窗台瓷砖粘贴', '1.工作内容：完成墙面墙砖所需的材料运输、基层处理、砖洇水、背胶、必要的墙砖现场切割、结合层搅拌、开孔、墙面砖黏贴等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（加建筑胶）或专用固化剂；
5.综合考虑:按图铺贴、切割开孔、防护材料、防空鼓措施、超高降效、配合材料下单等费用；', 'm2', 80.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-038', '泥水工', '墙面饰面-零星瓷砖粘贴', '1.工作内容：完成墙面墙砖所需的材料运输、基层处理、砖洇水、背胶、必要的墙砖现场切割、结合层搅拌、开孔、墙面砖黏贴等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（加建筑胶）或专用固化剂；
5.综合考虑:按图铺贴、切割开孔、防护材料、防空鼓措施、超高降效、配合材料下单等费用；', 'm2', 90.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-039', '泥水工', '墙面饰面-墙柱面石材铺贴', '1.工作内容：完成墙面湿贴/胶贴石材所需的材料运输、基层处理、必要的石材现场切割、打磨、开孔、安装等一切工作；
2.嵌缝材料种类:专用勾缝剂填缝；
3.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
4.基层处理:素水泥浆纵横各扫一道（加建筑胶）或专用固化剂；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:按图铺贴、切割开孔、防护材料、防空鼓措施、超高降效、配合材料下单等费用；', 'm2', 85.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-040', '泥水工', '墙面饰面-石材窗台铺贴', '1.工作内容：完成石材窗台所需的材料运输、基层处理、必要的石材现场切割、打磨、开孔、安装等一切工作；
2.嵌缝材料种类:专用勾缝剂填缝；
3.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
4.基层处理:素水泥浆纵横各扫一道（加建筑胶）或专用固化剂；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:按图铺贴、切割开孔、防护材料、防空鼓措施、超高降效、配合材料下单等费用；', 'm2', 96.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-041', '泥水工', '墙面饰面-零星石材铺贴', '1.工作内容：完成零星石材所需的材料运输、基层处理、必要的石材现场切割、打磨、开孔、安装等一切工作；
2.结合层厚度、材料品种:专用瓷砖胶/水泥沙结合层；
3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（加建筑胶）或专用固化剂；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:按图铺贴、切割开孔、防护材料、防空鼓措施、超高降效、配合材料下单等费用；', 'm2', 128.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-042', '泥水工', '墙面饰面-湿挂墙身石材', '1.工作内容：完成墙面湿挂石材（造型、零星项目）所需的材料运输、基层处理、必要的石材现场切割、打磨、开孔、安装等一切工作；
2.嵌缝材料种类:专用勾缝剂填缝；
3.挂件材质品种:水泥钢射钉/螺栓、铜丝及镀铜扣片等；
4.基层处理:素水泥浆纵横各扫一道（加建筑胶）或专用固化剂；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:按图铺贴、切割开孔、钻孔成槽、防护材料、防空鼓措施、安装膨胀螺栓、超高降效、配合材料下单等费用；', 'm2', 110.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-043', '泥水工', '墙面饰面-干挂墙身石材（常规）', '1.工作内容：完成墙面干挂石材所需的材料运输、基层处理、必要的石材现场切割、打磨、开孔、安装等一切工作；
2.挂件材质品种:不锈钢挂件，符合设计及规范要求；
3.嵌缝材料种类:专用填缝剂填缝；
4.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
5.综合考虑:深化排版、切割开孔、防锈油漆、超高降效、配合材料下单等费用；', 'm2', 110.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-044', '泥水工', '墙面饰面-干挂墙身零星/造型石材', '1.工作内容：完成墙面干挂墙身零星/造型石材所需的材料运输、基层处理、必要的石材现场切割、打磨、开孔、安装等一切工作；
2.挂件材质品种:不锈钢挂件，符合设计及规范要求；
3.嵌缝材料种类:专用填缝剂填缝；
4.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
5.综合考虑:深化排版、切割开孔、防锈油漆、超高降效、配合材料下单等费用；', 'm2', 126.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-045', '泥水工', '墙面饰面-墙面石材装饰线 50mm宽以内', '1.工作内容：完成墙面石材装饰线所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2.面层材料规格、品种:50mm宽以内石材装饰线；
3.安装方式:专用胶粘贴或水泥砂浆铺贴；
4.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
5.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效、配合材料下单等费用；', 'm', 13.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-046', '泥水工', '墙面饰面-墙面石材装饰线 100mm宽以内', '1.工作内容：完成墙面石材装饰线所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2.面层材料规格、品种:100mm宽以内石材装饰线；
3.安装方式:专用胶粘贴或水泥砂浆铺贴；
4.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
5.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效、配合材料下单等费用；', 'm', 16.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-047', '泥水工', '墙面饰面-墙面石材装饰线 150mm宽以内', '1.工作内容：完成墙面石材装饰线所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2.面层材料规格、品种:150mm宽以内石材装饰线；
3.安装方式:专用胶粘贴或水泥砂浆铺贴；
4.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
5.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效、配合材料下单等费用；', 'm', 24.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-048', '泥水工', '墙面饰面-干挂石材装饰线 50mm宽以内', '1.工作内容：完成墙面石材装饰线所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2.面层材料规格、品种:50mm以内石材装饰线；
3.挂件材质品种:不锈钢挂件，符合设计及规范要求；
4.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
5.综合考虑:基层处理、装饰线造型、直线/弧线、安装固定方式、超高降效、配合材料下单等费用；', 'm', 20.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-049', '泥水工', '墙面饰面-干挂石材装饰线 100mm宽以内', '1.工作内容：完成墙面石材装饰线所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2.面层材料规格、品种:100mm宽以内石材装饰线；
3.挂件材质品种:不锈钢挂件，符合设计及规范要求；
4.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
5.综合考虑:基层处理、装饰线造型、直线/弧线、安装固定方式、超高降效、配合材料下单等费用；', 'm', 26.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-050', '泥水工', '墙面饰面-干挂石材装饰线 150mm宽以内', '1.工作内容：完成墙面石材装饰线所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2.面层材料规格、品种:150mm宽以内石材装饰线；
3.挂件材质品种:不锈钢挂件，符合设计及规范要求；
4.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
5.综合考虑:基层处理、装饰线造型、直线/弧线、安装固定方式、超高降效、配合材料下单等费用；', 'm', 34.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-051', '泥水工', '墙面饰面-石材/钢质装饰件', '1.工作内容：完成墙面石材装饰件所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2.结合层厚度、材料品种:专用粘合剂；
3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（符合设计要求）；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:按图铺贴、切割开孔、防护材料、超高降效等费用；', '件', 57.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-052', '泥水工', '墙面饰面-踢脚线石材粘贴', '1.工作内容：完成墙面石材踢脚线所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2.嵌缝材料种类:专用勾缝剂填缝；
3.基层处理:素水泥浆纵横各扫一道（加建筑胶）或专用固化剂；
4.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
5.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm', 16.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-053', '', '墙面饰面-干挂踢脚线石材', '1.工作内容：完成墙面石材踢脚线所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2.挂件材质品种:不锈钢挂件，符合设计及规范要求；
3.嵌缝材料种类:专用填缝剂填缝；
4.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
5.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm', 28.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-054', '泥水工', '墙面饰面-踢脚线瓷砖粘贴', '1.工作内容：完成墙面块料踢脚线所需的材料运输、基层处理、必要的块料现场切割、打磨、安装等一切工作；
2.嵌缝材料种类:专用勾缝剂填缝；
3.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）、刷专用界面剂；
4.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm', 13.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-055', '泥水工', '墙面饰面-马赛克', '1.工作内容：完成墙面马赛克所需的材料运输、基层处理、必要的马赛克现场加工、结合层搅拌、开孔、黏贴、填缝等一切工作；
2.马赛克规格：300*300mm/片；
3.综合考虑:按图铺贴、切割开孔、防护材料、超高降效、配合材料下单等费用；', 'm2', 69.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-056', '泥水工', '墙面饰面-墙身石材灯槽 展开宽度500mm（含）以内', '1.工作内容：完成墙面石材灯槽线所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2、规格：展开宽度500mm（含）以内；
3.挂件材质品种:不锈钢挂件，符合设计及规范要求；
4.嵌缝材料种类:专用填缝剂填缝；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:灯槽造型及宽度、封边填缝、刷防护涂料、超高降效、配合材料下单等费用；', 'm', 46.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-057', '泥水工', '墙面饰面-墙身石材灯槽 展开宽度500mm以外', '1.工作内容：完成墙面石材灯槽线所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2、规格：展开宽度500mm以外；
3.挂件材质品种:不锈钢挂件，符合设计及规范要求；
4.嵌缝材料种类:专用填缝剂填缝；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:灯槽造型及宽度、封边填缝、刷防护涂料、超高降效、配合材料下单等费用；', 'm', 69.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-058', '泥水工', '墙面饰面-石材洗手台', '1.工作内容：完成石材洗手台所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2.挂件材质品种:不锈钢挂件，符合设计及规范要求；
3.嵌缝材料种类:专用填缝剂填缝；
4.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
5.综合考虑:深化排版、切割开孔、防锈油漆、超高降效、配合材料下单等费用；', 'm2', 172.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-059', '泥水工', '墙面饰面-石材门套粘贴', '1.工作内容：完成石材门套所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2.结合层厚度、材料品种:专用石材粘合剂3.嵌缝材料种类:专用勾缝剂填缝；
4.基层处理:素水泥浆纵横各扫一道（加建筑胶）或专用固化剂；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:按图造型、切割开孔、防护材料、超高降效等、配合材料下单等费用；', 'm2', 120.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-060', '泥水工', '墙面饰面-石材门套干挂', '1.工作内容：完成石材门套所需的材料运输、基层处理、必要的石材现场切割、打磨、安装等一切工作；
2.挂件材质品种:不锈钢挂件，符合设计及规范要求；
3、嵌缝材料种类:专用填缝剂填缝；
4、防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
5.综合考虑:深化排版、切割开孔、防锈油漆、超高降效、配合材料下单等费用；', 'm2', 172.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-061', '泥水工', '门、窗填缝', '1.工作内容：完成门、窗填缝所需的材料运输、基层处理等一切工作；
1.部位：门窗洞口内及收边
2.嵌缝、塞口：底部防水砂浆填塞,两侧及上部发泡剂填塞
3.尺寸：按门窗洞口考虑', 'm2', 12.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'NS-062', '泥水工', '天花-水泥砂浆找平', '1.工作内容：包含完成天花找平所需的场地清理、水泥砂浆搅拌、材料运输、超高降效等费用等一切工作；
2.水泥砂浆厚度：20mm以内；配合比需满足施工要求；
3.综合考虑:基层清理、抹面压光、压防滑槽、超高降效等费用；', 'm2', 20.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'FS-063', '防水工', '防水砂浆', '1.工作内容：包含完成地面防水所需的场地清理、材料搅拌、运输、抹浆等一切工作；
2.20mm1:2.5防水砂浆内掺3%防水粉；
3.位置：水沟内部等；
4.综合考虑:基层类型、平面/立面、抹面压光、超高降效等费用；', 'm2', 20.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'FS-064', '防水工', '水泥砂浆防水保护层', '1.工作内容：包含完成地面防水所需的场地清理、材料搅拌、运输、抹浆等一切工作；
2.材料种类、强度等级:1:3干硬性水泥砂浆（WS）【按实】；
3.材料厚度:20mm；
4.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）；
5.综合考虑:基层类型、平面/立面、抹面压光、超高降效等费用；', 'm2', 13.22, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'FS-065', '防水工', '1.5mm厚聚合物水泥防水涂料
（II型）', '1.工作内容：完成地面防水所需的场地清理（满足施工要求）、阴角水泥砂浆圆边处理、材料运输、1.5mm厚聚合物水泥防水涂料（按实）施工、闭水试验等一切工作；
2.防水膜品种:聚合物水泥防水涂料（II型）
3.涂膜厚度:1.5mm
4.综合考虑:施工部位、平面/立面、基层处理剂、搭接
及附加层工程量、超高降效等增加费', 'm2', 12.08, '按展开面积');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('泥水班组', 'FS-066', '防水工', '2.0mm单组份聚氨酯防水涂料
（I型）', '1.工作内容：完成地面防水所需的场地清理（满足施工要求）、阴角水泥砂浆圆边处理、材料运输、2.0mm单组份聚氨酯防水涂料（按实）施工、闭水试验等一切工作；
2.防水膜品种:聚合物水泥防水涂料（II型）
3.涂膜厚度:2mm
4.综合考虑:施工部位、平面/立面、基层处理剂、搭接
及附加层工程量、超高降效等增加费', 'm2', 13.23, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-01', '木工', '地面基层-木地板龙骨及基层', '1.工作内容：完成地面夹板封板所需的定位、找平、材料切割加工、材料运输、安装等一切工作；
2.材质：各规格阻燃夹板；
3.基层：难燃木龙骨
4.综合考虑:龙骨间距、防护材料、超高降效等费用', 'm2', 21.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-02', '木工', '地面饰面-室内木地板（常规）', '1.工作内容：完成室内木地板所需的材料运输、拼接、固定、材料切割加工、安装、开孔等一切工作；
2.材质：各类规格室内木地板；
3.基层：聚乙烯塑料泡沫垫
4.防潮材料种类、规格:防潮纸
5.综合考虑:收口条、防护材料、超高降效等费用；', 'm2', 23.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-03', '木工', '地面饰面-户外木地板（常规）', '1.工作内容：完成户外木地板所需的材料运输、拼接、定位、固定、材料切割加工、安装、开孔等一切工作；
2.材质：各类规格户外木地板；
3.综合考虑:收口条、防护材料、超高降效等费用；', 'm2', 34.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-04', '木工', '墙面-墙纸/墙布（硬扪）', '1.工作内容：完成墙面墙纸/墙布硬扪所需的材料运输、基层板材加工、线条收边、墙纸/墙布硬扪、安装施工等一切工作；
2.面层材料种类、规格:墙布
3.基层材料种类、规格:阻燃夹板
4.综合考虑:基层类型、制作硬包板、安装及修整硬包墙面、超高降效等费', 'm2', 70.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-05', '木工', '墙面-墙纸/墙布（软包）', '1.工作内容：完成墙面墙纸/墙布软包所需的材料运输、基层板材加工、线条收边、软包基层、墙纸/墙布加工、安装施工等一切工作；
2.面层材料种类、规格:墙布
3.基层材料种类、规格:9mm阻燃夹板
4.综合考虑:基层类型、软包填充物、制作硬包板、安装及修整软包墙面、超高降效等费', 'm2', 75.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-06', '木工', '墙面木装饰线 50mm宽以内', '1.工作内容：完成墙面木装饰线所需的材料运输、基层处理、必要的踢脚线现场加工，安装等一切工作；
2.装饰线宽度:50mm【按实】；
3.面层材料规格、品种:木装饰线【按实】；
4.安装方式:专用胶粘贴或钉装；
5.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效等费用；', 'm', 10.76, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-07', '木工', '墙面木装饰线 100mm宽以内', '1.工作内容：完成墙面木装饰线所需的材料运输、基层处理、必要的踢脚线现场加工，安装等一切工作；
2.装饰线宽度:100mm【按实】；
3.面层材料规格、品种:木装饰线【按实】；
4.安装方式:专用胶粘贴或钉装；
5.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效等费用；', 'm', 12.61, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-08', '木工', '墙面木装饰线 150mm宽以内', '1.工作内容：完成墙面木装饰线所需的材料运输、基层处理、必要的踢脚线现场加工，安装等一切工作；
2.装饰线宽度:150mm【按实】；
3.面层材料规格、品种:木装饰线【按实】；
4.安装方式:专用胶粘贴或钉装；
5.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效等费用；', 'm', 14.55, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-09', '木工', '墙面-木踢脚线', '1.工作内容：完成墙面木踢脚线所需的材料运输、基层处理、必要的踢脚线现场加工，安装等一切工作；
2.踢脚线高度:100mm以内
3.面层材料规格、品种:木踢脚线
4.综合考虑:凹槽造型、踢脚线卡件、固定件、封边线、超高降效等费用', 'm', 10.91, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-010', '木工', '墙面-木饰面（造型/零星项目）', '1.工作内容：完成墙面木饰面（造型/零星项目）所需的材料运输、基层处理、必要的木饰面现场加工、开孔、安装等一切工作；
2.面层材料种类、规格:木饰面（造型/零星项目）
3.综合考虑:基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 48.05, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-011', '木工', '墙面-木饰面（常规）', '1.工作内容：完成墙面木饰面所需的材料运输、基层处理、必要的木饰面现场加工、开孔、安装等一切工作；
2.面层材料种类、规格:木饰面（常规）
3.综合考虑:基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 36.96, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-012', '木工', '墙面-靠墙扶手', '1.工作内容：完成靠墙扶手所需的现场放线、材料运输、钻孔、不锈钢安装及相关小配件安装等内容；
2.其他：需配合项目部现场下单工作；
3.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效等费用；', 'm', 20.04, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-013', '木工', '墙面PVC收边条', '1.工作内容：完成墙面PVC收边条所需的一切工作内容；
2.面层材料规格、品种:PVC收边条；
3.安装方式:专用胶粘贴或钉装；
4.综合考虑:基层处理、规格尺寸、阴角/阳角、直线/弧线、超高降效等费用；', 'm', 2.08, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-014', '木工', '墙面基层-轻钢龙骨/夹板基层', '1.工作内容：完成墙面轻钢龙骨/夹板基层所需材料运输、放线定位、防腐处理、必要的板材加工、切割、校平、安装固定等一切工作；
2.基层材料种类、规格:单层难燃夹板【按实】；
3.龙骨材料种类、规格:镀锌钢龙骨、规格间距符合图纸
要求
4.综合考虑:基层清理、封边填缝、刷防护涂料、超高降效等费用', 'm2', 47.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-015', '木工', '墙面基层-木龙骨/夹板基层', '1.工作内容：完成墙面木龙骨/夹板基层所需材料运输、放线定位、防腐处理、必要的板材加工、切割、校平、安装固定等一切工作；
2.基层材料种类、规格:单层难燃夹板【按实】；
3.龙骨材料种类、规格:双向木龙骨、规格间距符合图纸
要求
4.综合考虑:基层清理、封边填缝、刷防护涂料、超高降效等费用', 'm2', 46.56, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-016', '木工', '墙柱面无龙骨基层板', '1.工作内容：完成墙柱面无龙骨基层板所需材料运输、放线定位、防腐处理、必要的板材加工、切割、校平、安装固定等一切工作；
2.基层材料种类、规格:夹板/石膏板【按实】；
3.综合考虑:基层清理、钉贴方式、封边填缝、刷防护涂料、超高降效等费用', 'm2', 23.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-017', '木工', '墙柱面基层板 每增减一层', '1.工作内容：墙柱面基层板 每增减一层所需材料运输、放线定位、防腐处理、必要的板材加工、切割、校平、安装固定等一切工作；
2.基层材料种类、规格:夹板/石膏板【按实】；
3.综合考虑:基层清理、钉贴方式、封边填缝、刷防护涂料、超高降效等费用', 'm2', 14.94, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-018', '木工', '墙面基层-门框夹板', '1.工作内容：完成门框夹板基层所需的材料运输、防线定位、防腐处理、必要的板材加工、切割、校平、安装固定、水泥砂浆浇灌等一切工作；
2.基层材料种类、规格:9mm难燃夹板【按实】；
3.龙骨材料种类、规格:双向木龙骨、规格间距符合图纸
要求
4.综合考虑:防腐涂料、超高降效等费', 'm2', 57.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-019', '木工', '轻钢龙骨隔墙 100mm以内', '1.工作内容：完成墙面100隔墙轻钢龙骨所需材料运输、现场放线定位、必要的现场龙骨切割、安装、固定等一切工作；
2.隔墙类型:双面单层板隔墙【按实】；
3.隔墙厚度:100mm以内
4.基层板材料种类、规格:双面阻燃夹板【按实】
5.龙骨材料种类、规格:镀锌轻钢龙骨、规格间距符合图纸要求
6.综合考虑:刷防腐涂料、嵌缝、超高降效等费用', 'm2', 64.4, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-020', '木工', '轻钢龙骨隔墙 200mm以内', '1.工作内容：完成墙面100隔墙轻钢龙骨所需材料运输、现场放线定位、必要的现场龙骨切割、安装、固定等一切工作；
2.隔墙类型:双面单层板隔墙【按实】；
3.隔墙厚度:200mm以内
4.基层板材料种类、规格:双面阻燃夹板【按实】
5.龙骨材料种类、规格:镀锌轻钢龙骨、规格间距符合图纸要求
6.综合考虑:刷防腐涂料、嵌缝、超高降效等费用', 'm2', 84.53, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-021', '木工', '墙面隔墙-隔音棉', '1.工作内容：完成墙面隔墙/或隔音墙面所需的材料运输、必要的材料切割、安装固定等一切工作；
2.材料种类、规格:100mm隔音棉
3.材料品种.规格.品牌.颜色:符合设计及规范要求
4.综合考虑:刷防腐涂料、嵌缝、超高降效等费用', 'm2', 8.2, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-022', '木工', '墙面隔墙-基层板每增加减一层', '1.工作内容：完成隔墙封单面基层板所需材料运输、放线定位、防腐处理、必要的板材加工、切割、校平、安装固定等一切工作；
2.基层板材料种类、规格:9mm阻燃夹板
3.综合考虑:刷防腐涂料、嵌缝、超高降效等费用', 'm2', 17.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-023', '木工', '墙面装饰板灯槽 
展开宽度500mm（含）以内', '1.工作内容：完成墙面装饰板灯槽所需的一切工作内容；
2.灯槽展开尺寸:200mm+300mm【按实】；
3.面层材料规格、品种:9mm石膏板+9mm阻燃夹板【按实】；
4.龙骨材质品种:国标镀锌型材骨架，符合设计及规范要求；
5.综合考虑:灯槽造型及宽度、封边填缝、刷防护涂料超高降效等费；', 'm', 42.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-024', '木工', '墙面装饰板灯槽 
展开宽度500mm以外', '1.工作内容：完成墙面装饰板灯槽所需的一切工作内容；
2.灯槽展开尺寸:200mm+500mm【按实】
3.面层材料规格、品种:9mm石膏板+9mm阻燃夹板；
4.龙骨材质品种:国标镀锌型材骨架，符合设计及规范要求；
5.综合考虑:灯槽造型及宽度、封边填缝、刷防护涂料超高降效等费；', 'm', 46.8, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-025', '木工', '石膏板吊顶 平面', '1.工作内容：完成安装石膏板吊顶所需材料运输、板材切割加工、开孔、防腐处理等一切工作；
2.面层材料品种、规格:9mm石膏板【按实】；
3.底层材料品种、规格:9mm石膏板【按实】；
4.龙骨材料种类、规格:轻钢龙骨、间距符合图纸要求
5.吊顶形式、吊杆规格、高度:符合设计及施工要求
6.综合考虑:石膏绷带，天花开孔（含检修口、灯位、风口等）及四边贴美纹纸、专用收口条、刷防护涂料、超高降效等费用', 'm2', 68.0, '按展开面积计算');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-026', '木工', '石膏板吊顶 立面', '1.工作内容：完成安装石膏板吊顶 所需材料运输、板材切割加工、开孔、防腐处理等一切工作；
2.面层材料品种、规格:9mm石膏板【按实】；
3.底层材料品种、规格:9mm阻燃夹板【按实】；
4.龙骨材料种类、规格:轻钢龙骨、间距符合图纸要求
5.综合考虑:石膏绷带，天花开孔（含检修口、灯位、风口等）及四边贴美纹纸、专用收口条、刷防护涂料、超高降效等费用', 'm2', 65.0, '按展开面积计算');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-027', '木工', '天棚基层板 无龙骨型', '1.工作内容：完成安装石膏板吊顶 所需材料运输、板材切割加工、开孔、防腐处理等一切工作；
2.面层材料品种、规格:9mm石膏板【按实】；
3.综合考虑:钉贴方式及部位、石膏绷带，天花开孔（含
检修口、灯位、风口等）及四边贴美纹纸、专用收口条、刷防护涂料、超高降效等费用', 'm2', 19.43, '按展开面积计算');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-028', '木工', '天棚基层板 每增减一层', '1.工作内容：完成安装石膏板吊顶 所需材料运输、板材切割加工、开孔、防腐处理等一切工作；
2.增加材料品种、规格:9mm石膏板【按实】；
3.综合考虑:石膏绷带，天花开孔（含检修口、灯位、风口等）及四边贴美纹纸、专用收口条、刷防护涂料、超高降效等费用', 'm2', 13.46, '按展开面积计算');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-029', '木工', '天花饰面-木饰面', '1.工作内容：完成安装天花木饰面所需材料运输、板材切割加工、开孔、防腐处理等一切工作；
2.需配合其他专业单位（消防、空调、机电）定位开孔；
3.面层材料种类、规格:木饰面（常规）
4.综合考虑:基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 66.7, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-030', '木工', '天棚灯槽展开宽度500mm（含）以内', '1.工作内容：完成直型灯槽所需的材料运输、定位、板材切割加工、固定安装，防腐处理等一切工作；
2.灯槽展开尺寸:200mm+100mm
3.面层材料品种、规格:9mm石膏板
4.面层材料品种、规格:9mm阻燃夹板
5.龙骨材料种类、规格:轻钢龙骨、间距符合图纸要求
6.综合考虑:石膏绷带、直形、刷防护涂料、超高降效等费用
7.弧形增加费按20%综合考虑', 'm', 42.9, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-031', '木工', '天棚灯槽展开500mm以外', '1.工作内容：完成直型灯槽所需的材料运输、定位、板材切割加工、固定安装，防腐处理等一切工作；
2.灯槽展开尺寸:300mm+120mm
3.面层材料品种、规格:9mm石膏板
4.面层材料品种、规格:9mm阻燃夹板
5.龙骨材料种类、规格:轻钢龙骨、间距符合图纸要求
6.综合考虑:石膏绷带、直形/弧形、刷防护涂料、超高降效等费用
7.弧形增加费按20%综合考虑', 'm', 49.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-032', '木工', '窗帘盒', '1.工作内容：完成窗帘盒所需的材料运输、定位、板材切割加工、固定安装，防腐处理等一切工作；
2.窗帘盒展开尺寸:200mm+100mm
3.面层材料品种、规格:9mm石膏板
4.面层材料品种、规格:9mm阻燃夹板
5.龙骨材料种类、规格:轻钢龙骨、间距符合图纸要求
6.综合考虑:石膏绷带、直形/弧形、刷防护涂料、超高降效等费用
7.高度超过200mm,按比例换算', 'm', 42.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-033', '木工', '天花凹槽', '1.工作内容：完成天花凹槽所需的材料运输、定位、板材切割加工、固定安装，防腐处理等一切工作；
1.凹槽规格尺寸:综合考虑；
2.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效等费用；', 'm', 7.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-034', '木工', '天棚PVC保护条', '1.工作内容：完成天棚PVC保护条所需的材料运输、定位、基层安装、必要的金属切割加工、固定安装，防腐处理等一切工作；
2.面层材料规格、品种:PVC收边条；
3.安装方式:专用胶粘贴或钉装；
4.综合考虑:基层处理、规格尺寸、阴角/阳角、直线/弧线、超高降效等费用；', 'm', 3.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-035', '木工', '天花装饰线-木装饰线', '1.工作内容：完成天花木装饰线所需的材料运输、定位、基层安装、必要的木装饰线切割加工、固定安装，防腐处理等一切工作；
2.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效等费用；
3.木装饰线规格：100mm以内，超出100mm以外，按比例换算；', 'm', 10.58, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-036', '木工', '天花-检修口', '1.工作内容：完成天花检修口所需的材料运输、定位、天花开孔、安装成品检修口、检修口封板处理等一切工作；
2.检修口规格：600*600mm以内；
3.综合考虑:基层处理、安装方式、超高降效等费用；', '个', 28.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-037', '木工', '天花空调风口（线型）', '1.工作内容：完成天花空调风口所需材料运输、定位、天花开孔、收边安装成品空调风口等一切工作；
2.空调风口规格：300mm以内；
3.综合考虑:基层处理、安装方式、超高降效等费用；', 'm2', 40.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-038', '木工', '门工程-门框安装（不带门扇）', '1.工作内容：完成门框安装所需的放线定位、材料运输、基层处理、必要的板材切割加工、防腐、填缝、安装固定等一切工作；
2.面层材料种类、规格:木饰面
3.基层材料种类、规格:9mm难燃夹板
4.龙骨材料种类、规格:双向木龙骨、规格间距符合图纸
要求
5.综合考虑:防腐涂料、超高降效等费', 'm2', 90.91, '按展开面积计算');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-039', '木工', '门工程-门框带门扇安装（木质）平开/推拉', '1.工作内容：完成门框带门扇安装（木质）平开所需的放线定位、材料运输、基层处理、必要的木门合页止口（个别）、隔音条、防腐处理、填缝、门框、门扇固定安装等一切工作；
2.其他：面积按照门框最外边线立面投影计算；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 57.32, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-040', '木工', '门工程-门框带门扇安装（钢质）平开', '1.工作内容：完成门框带门扇安装（钢质）平开所需的放线定位、材料运输、基层处理、隔音条、防腐处理、填缝、门框、门扇固定安装等一切工作；
2.其他：面积按照门框最外边线立面投影计算；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 57.32, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-041', '木工', '门工程-门框带门扇安装（木质）隐藏门', '1.工作内容：完成门框带门扇安装（木质）隐藏门所需的放线定位、材料运输、基层处理、轨道施工、隔音条、防腐处理、填缝、门框、门扇固定安装等一切工作；
2.其他：面积按照门框最外边线立面投影计算；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 57.32, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-042', '木工', '门五金工程-门锁（球形）简易', '1.工作内容：完成门锁（球形）简易所需的门锁安装、固定等一切工作；
2.其他：门锁开孔属供应商工作范畴 ；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', '套', 17.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-043', '木工', '门五金工程-门锁（把手）', '1.工作内容：完成门锁（把手）所需的门锁锁体、把手、侧装片安装、固定等一切工作；
2.其他：门锁开孔属供应商工作范畴；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', '套', 20.36, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-044', '木工', '门五金工程-门锁（智能门锁）', '1.工作内容：完成门锁（智能门锁）所需的门锁锁体、把手、侧装片安装、固定等一切工作；
2.其他：门锁开孔属供应商工作范畴；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', '套', 34.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-045', '木工', '门五金工程-闭门器（隐藏式）', '1.工作内容：完成闭门器（隐藏式）所需的闭门器安装、固定等一切工作；
2.其他：开孔属供应商工作范畴；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', '套', 48.3, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-046', '木工', '门五金工程-闭门器（明装式）', '1.工作内容：完成闭门器（明装式）所需的闭门器安装、固定等一切工作；
2.其他：开孔属供应商工作范畴；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', '套', 40.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-047', '木工', '门五金工程-电动闭门器', '1.工作内容：完成电动闭门器所需的现场定位、接线安装、闭门器安装、固定、调试等一切工作；
2.其他：开孔属供应商工作范畴；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', '套', 57.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-048', '木工', '门五金工程-拉手', '1.工作内容：完成拉手所需的拉手安装、固定等一切工作；
2.其他：开孔属供应商工作范畴；
3.规格：长度1500mm，超过此规格人工费按1.1系数计算；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', '套', 27.83, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-049', '木工', '门五金工程-残疾人扶手', '1.工作内容：完成残疾人扶手所需的墙面扶手（整套）现场定位、墙面开孔、安装、固定等一切工作；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', '套', 30.9, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-050', '木工', '门五金工程-猫眼', '1.工作内容：完成猫眼所需的猫眼安装、固定等一切工作；
2.其他：开孔属供应商工作范畴；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', '套', 6.19, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-051', '木工', '门五金工程-门顶', '1.工作内容：完成门顶所需的门顶现场定位、安装、固定等一切工作；
2.其他：开孔属供应商工作范畴；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', '套', 16.27, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-052', '木工', '门五金工程-暗插销', '1.工作内容：完成暗插销所需的暗插销现场定位、安装、固定等一切工作；
2.其他：开孔属供应商工作范畴；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', '套', 6.19, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('木工班组', 'YQ-053', '木工', '门五金工程-顺位器', '1.工作内容：完成顺位器所需的顺位器现场定位、安装、固定等一切工作；
2.其他：开孔属供应商工作范畴；
3.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', '套', 17.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('油漆班组', 'YQ-01', '油漆工', '墙面-艺术漆墙面', '1.工作内容：完成墙面艺术漆墙面所需的材料运输、清理墙面、修补墙面、刮腻子、打磨、艺术漆施工等一切工作；
2.刮腻子遍数:三遍
3.面漆涂料品种、喷刷遍数:乳胶漆两遍【甲供】
4.底漆涂料品种、喷刷遍数:乳胶漆一遍【甲供】
5.综合考虑:基层类型、油漆类型、喷涂方式、刷专用固化剂、砂纸磨平、PVC护角线、超高降效等增加费用', 'm2', 43.7, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('油漆班组', 'YQ-02', '油漆工', '墙面-乳胶漆', '1.工作内容：完成墙面乳胶漆所需的材料运输、清理墙面、修补墙面、刮腻子、打磨、乳胶漆施工等一切工作；
2.刮腻子遍数:三遍
3.面漆涂料品种、喷刷遍数:乳胶漆两遍【甲供】
4.底漆涂料品种、喷刷遍数:乳胶漆一遍【甲供】
5.综合考虑:基层类型、油漆类型、喷涂方式、刷专用固化剂、砂纸磨平、PVC护角线、超高降效等增加费用', 'm2', 25.3, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('油漆班组', 'YQ-03', '油漆工', '墙面-墙纸（不对花）', '1.工作内容：完成墙面墙纸所需的材料运输、清理墙面、修补墙面、刮腻子、打磨、基膜处理、墙纸施工等一切工作；
2.面层材料规格、品种:墙纸
3.粘贴层材料品种:专用壁纸胶、白乳胶
4.底胶品种、遍数:108胶:水：白乳胶=1:1:0.1
5.基础处理要求:墙纸专用基膜两遍
6.综合考虑:基层类型、砂纸抹平、排版裁剪、超高降效等费用', 'm2', 33.99, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('油漆班组', 'YQ-04', '油漆工', '墙面-墙纸（对花）', '1.工作内容：完成墙面墙纸所需的材料运输、清理墙面、修补墙面、刮腻子、打磨、基膜处理、墙纸施工等一切工作；
2.面层材料规格、品种:墙纸
3.粘贴层材料品种:专用壁纸胶、白乳胶
4.底胶品种、遍数:108胶:水：白乳胶=1:1:0.1
5.基础处理要求:墙纸专用基膜两遍
6.综合考虑:基层类型、砂纸抹平、排版裁剪、超高降效等费用', 'm2', 42.66, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('油漆班组', 'YQ-05', '油漆工', '墙面基层-水泥膏灰找平', '1.工作内容:完成墙面水泥膏灰找平所需材料运输、搅拌、找平等一切工作；
2.材料种类、强度等级:1:2.5水泥砂浆（WP）【按实】；
3.材料厚度:20mm；
4.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）；
5.其他：天花施工人工费按1.1系数计算；
6.综合考虑:基层类型、抹面压光、超高降效等费用；', 'm2', 11.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('油漆班组', 'YQ-06', '油漆工', '天花装饰线-石膏线', '1.工作内容：完成天花石膏装饰线所需的材料运输、定位、基层安装、必要的饰线切割加工、固定安装等一切工作；
2.安装方式:专用胶粘贴或钉装；
3.石膏装饰线规格：150mm以内
4.综合考虑:直线/弧线、超高降效等费用；
5.超出150mm以外，人工费按比例换算；', 'm', 9.78, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('油漆班组', 'YQ-07', '油漆工', '天棚-乳胶漆饰面', '1.工作内容：完成天花乳胶漆所需的材料运输、基层处理、腻子两遍、打磨、乳胶漆饰面一底两面等一切工作；
2.刮腻子遍数:三遍
3.面漆涂料品种、喷刷遍数:乳胶漆两遍【甲供】
4.底漆涂料品种、喷刷遍数:乳胶漆一遍【甲供】
5.综合考虑:基层类型、油漆类型、喷涂方式、刷专用固化剂、砂纸磨平、PVC护角线、超高降效等增加费用', 'm2', 24.04, '按展开面积计算');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('油漆班组', 'YQ-08', '油漆工', '天棚-乳胶漆饰面（防水）', '1.工作内容：完成天花乳胶漆所需的材料运输、基层处理、腻子两遍、打磨、乳胶漆饰面一底两面等一切工作；
2.刮腻子遍数:三遍
3.面漆涂料品种、喷刷遍数:乳胶漆两遍【甲供】
4.底漆涂料品种、喷刷遍数:乳胶漆一遍【甲供】
5.综合考虑:基层类型、油漆类型、喷涂方式、刷专用固化剂、砂纸磨平、PVC护角线、超高降效等增加费用', 'm2', 24.04, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('油漆班组', 'YQ-09', '油漆工', '天棚喷黑色油漆', '1.工作内容：完成天棚喷黑色油漆所需的材料运输、基层处理、打磨、天棚喷黑色油漆施工等一切工作；
2.涂料品种:乳胶漆底漆【甲供】；
3.喷涂遍数:三遍；
4.综合考虑:基层类型、油漆类型、喷涂方式、超高降效等费用；', 'm2', 7.71, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('油漆班组', 'YQ-010', '油漆工', '天棚-墙纸饰面', '1.工作内容：完成天花墙纸所需的材料运输、清理墙面、修补墙面、刮腻子、打磨、基膜处理、墙纸施工等一切工作；
2.面层材料规格、品种:墙纸
3.粘贴层材料品种:专用壁纸胶、白乳胶
4.底胶品种、遍数:108胶:水：白乳胶=1:1:0.1
5.基础处理要求:墙纸专用基膜两遍
6.综合考虑:基层类型、砂纸抹平、排版裁剪、超高降效等费用', 'm2', 33.99, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-01', '铁工', '地面基层-钢架支撑', '1.工作内容：完成地面钢架龙骨所需的定位、找平、钢架切割加工、材料运输、焊接、刷防锈漆等一切工作；
2、材质：镀锌钢材；
3.支撑高度：500mm以内;
4.综合考虑:深化排版、切割开孔、防锈油漆、超高降效等费；', 'm2', 86.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-02', '铁工', '地面饰面-不锈钢装饰线（20mm以内）', '1.工作内容：完成地面不锈钢装饰线所需的定位、必要的材料现场切割加工、安装、固定等一切工作；
2.面层材料规格、品种:不锈钢装饰线【按实】；
3.安装方式:专用胶粘贴或钉装；
4.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效等费用；
5.其他工作：专业分包配合材料下单；', 'm', 13.8, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-03', '铁工', '墙面基层-钢架活动门、管井、消防栓暗门', '1.工作内容：完成钢架活动门所需的材料运输，放线定位、必要的钢材现场加工、焊制、安装、油漆等一切工作；
2.钢架门规格：1800*700mm以内；
3.龙骨材料种类、规格:镀锌型钢龙骨
4.综合考虑:门轴、拉手等五金配件', 'm2', 172.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-04', '铁工', '墙面基层-钢架', '1.工作内容：完成墙面钢架所需的钢架定位、材料运输、材料切割加工、焊制安装、开孔、刷漆等一切工作；
2.材质：镀锌钢材；
3.计算规格：按照立面投影面积计算；
4.综合考虑:深化排版、切割开孔、防锈油漆、超高降效等费；', 'm2', 92.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-05', '铁工', '石材洗手台-钢架', '1.工作内容：完成石材洗手台所需的钢架定位、材料运输、材料切割加工、焊制安装、开孔、刷漆等一切工作；
2.面层材料规格、品种:20mm厚石材【按实】；
3.挂件材质品种:不锈钢挂件，符合设计及规范要求；
4.嵌缝材料种类:专用填缝剂填缝；
5.防护层材料种类:背面、侧面刷背胶、面层刷防污剂；
6.综合考虑:深化排版、切割开孔、防锈油漆、超高降效等费；', 'm2', 92.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-06', '木工', '墙面金属装饰线 
长边100mm（含）以内', '1.工作内容：完成墙面金属装饰线所需的材料材料运输、基层板施工、必要的踢脚线现场加工，安装等一切工作；
2.装饰线展开尺寸:15mm+50mm+15mm【按实】；
3.面层材料规格、品种:不锈钢装饰线【按实】；
4.安装方式:专用胶粘贴或钉装；
5.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效等费用；', 'm', 15.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-07', '木工', '墙面金属装饰线 
长边150mm（含）以内', '1.工作内容：完成墙面金属装饰线所需的材料材料运输、基层板施工、必要的踢脚线现场加工，安装等一切工作；
2.装饰线展开尺寸:15mm+100mm+15mm【按实】；
3.面层材料规格、品种:不锈钢装饰线【按实】；
4.安装方式:专用胶粘贴或钉装；
5.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效等费用；', 'm', 16.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-08', '木工', '墙面-金属踢脚线', '1.工作内容：完成墙面金属踢脚线所需的材料运输、基层板施工、必要的踢脚线现场加工，安装等一切工作；
2.其他工作：专业分包配合材料下单；
3.踢脚线规格：H200mm以内，超过此规格按实际面积计算；
4.综合考虑:基层处理、规格尺寸、阴角/阳角、直线/弧线、超高降效等费用；', 'm', 13.8, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-09', '木工', '墙面-不锈钢（造型/零星项目金属类）', '1.工作内容：完成墙面不锈钢（金属类造型以及零星项目）所需的材料运输、基层处理、必要的木饰面现场加工、开孔、安装等一切工作；
2.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 66.97, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-010', '木工', '墙面-不锈钢（常规金属类）', '1.工作内容：完成墙面不锈钢（金属类）所需的材料运输、基层处理、必要的木饰面现场加工、开孔、安装等一切工作；
2.综合考虑:基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 51.2, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-011', '木工', '墙柱干挂金属饰面', '1.工作内容：完成墙柱干挂金属饰面所需的材料运输、基层处理、必要的木饰面现场加工、开孔、安装等一切工作；
2.面层材料规格、品种:2.5mm金属饰面【按实】；
3.挂件材质品种:不锈钢挂件，符合设计及规范要求；
4.龙骨材质品种:国标镀锌型材骨架，符合设计及规范要求；
5.基层处理:素水泥浆纵横各扫一道（内掺建筑胶）、刷专用界面剂；
6.综合考虑:基层类型、封边填缝、刷防护涂料、超高降效等费用；', 'm2', 74.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-012', '铁工', '天花转换层', '1.工作内容：完成天花钢架转换层所需的钢架定位、材料运输、材料切割加工、焊制安装、开孔、刷漆等一切工作；
2.材质：镀锌钢材；
3.计算规格：按照平面投影面积计算；
4.综合考虑:深化排版、切割开孔、防锈油漆、超高降效等费；', 'm2', 63.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-013', '铁工', '天花反支撑', '1.工作内容：在转换层基础上完成天花反支撑所需的吊杆定位、材料运输、材料切割加工、焊制安装、开孔、刷漆等一切工作；
2.材质：镀锌钢材；
3.计算规格：按照平面投影面积计算；
4.综合考虑:深化排版、切割开孔、防锈油漆、超高降效等费；', 'm2', 28.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-014', '铁工', '天花大型灯具加固点', '1.工作内容：完成大型灯具钢架支撑加固所需的定位、材料运输、材料切割加工、焊制安装、开孔、刷漆等一切工作；
2.其他工作：大型脚手架项目部负责，移动式脚手架由班组负责；
3.综合考虑:深化排版、切割开孔、防锈油漆、超高降效等费；', '处', 51.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-015', '铁工', '天花内导轨承重加固', '1.工作内容：完成天花钢架支撑所需的钢架定位、材料运输、材料切割加工、焊制安装、开孔、刷漆等一切工作；
2.其他：满足设计图纸要求所需的所有工作内容；
3.截面规格：400*400mm以内；
4.综合考虑:深化排版、切割开孔、防锈油漆、超高降效等费；', 'm', 48.3, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-016', '铁工', '天花饰面-金属面（不锈钢）', '1.工作内容：完成安装金属饰面所需的材料运输、金属材料局部切割加工、安装等一切工作
天棚类型:天棚金属饰面
2.面层材料品种、规格:金属饰面
3.综合考虑:基层处理、钉贴部位及方式、密缝收口、超高降效等费用', 'm2', 57.6, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-017', '铁工', '金属/玻璃吊顶', '1.工作内容：完成金属/玻璃吊顶所需的材料运输、金属材料局部切割加工、安装等一切工作；
2.天棚类型:不锈钢/玻璃吊顶【按实】；
3.面层材料品种、规格:2mm金属/玻璃【按实】；
4.龙骨材料种类、规格:轻钢龙骨、间距符合图纸要求；
5.吊顶形式、吊杆规格、高度:符合设计及施工要求；
6.综合考虑:金属带收口线、固定件、密封填缝、超高降效等费用；', 'm2', 60.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('铁工班组', 'TG-018', '', '天花装饰线-金属', '1.工作内容：完成天花金属装饰线所需的材料运输、定位、基层安装、必要的金属切割加工、固定安装，防腐处理等一切工作；
3.综合考虑:基层处理、装饰线造型、直线/弧线、超高降效等费用；
4.金属装饰线规格：100mm以内，超出100mm以外，人工费按比例换算；', 'm', 11.9, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('玻璃班组', 'BL-01', '玻璃工', '地面铺设-玻璃', '1.工作内容：包含完成玻璃地面所需的材料运输、放线定位、安装固定等一切工作；
2.基层：钢架支撑地面（其他工种完成）；
3.综合考虑:基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 45.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('玻璃班组', 'BL-02', '玻璃工', '墙面-亚克力板', '1.工作内容：完成墙面亚克力板所需的材料运输、基层处理、必要的板材现场加工、开孔、安装等一切工作；
2.面层材料种类、规格:亚克力板
3.综合考虑:基层类型、钉贴方式、封边填缝、超高降效
等费用', 'm2', 26.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('玻璃班组', 'BL-03', '玻璃工', '墙面-成品玻璃隔断', '1.工作内容：完成玻璃隔断所需的现场放线、材料运输、玻璃隔断安装、调平、打胶及相关小配件安装等内容；
2.综合考虑:隔断门、脚座、五金配件、超高降效等费用；', 'm2', 75.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('玻璃班组', 'BL-04', '玻璃工', '墙面-不锈钢+玻璃栏杆', '1.工作内容：完成栏杆所需的现场放线、材料运输、钻孔、不锈钢、玻璃、扶手安装及相关小配件安装等内容；
2.综合考虑:材料下单、超高降效等费用；', 'm', 75.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('玻璃班组', 'BL-05', '玻璃工', '墙面-镜子饰面', '1.工作内容：完成墙面镜子所需的材料运输、放线定位、玻璃安装固定等一切工作；
2.综合考虑:基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 56.82, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('玻璃班组', 'BL-06', '玻璃工', '墙面-玻璃饰面', '1.工作内容：完成墙面玻璃所需的材料运输、放线定位、玻璃安装固定等一切工作；
2.综合考虑:基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 56.82, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-01', '专业班组', '地面-塑胶地板', '1.工作内容：包含完成塑胶地板施工所需的场地清理、材料运输、拼接、材料切割、固定安装等一切工作；
2.其他：专业分包配合材料下单；
3.综合考虑:基层处理、超高降效等费用；', 'm2', 17.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-02', '专业班组', '地面饰面-地毯铺设（方块）', '1.工作内容：包含完成地面地毯所需的场地清理、定位、开孔、地毯施工安装等一切工作；
2.综合考虑:地毯卡条、超高降效等费用；
3.其他工作：专业分包配合材料下单；', 'm2', 17.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-03', '专业班组', '地面饰面-地毯铺设（满铺）', '1.工作内容：包含完成地面地毯所需的场地清理、定位、开孔、收边、地毯施工安装等一切工作；
2.综合考虑:地毯卡条、超高降效等费用；
3.其他工作：专业分包配合材料下单；', 'm2', 17.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-04', '专业班组', '地面饰面-防静电地板', '1.工作内容：包含完成防静电地面所需的材料运输、放线定位、钢骨架架设、校平、必要的地板切割加工、安装固定等一切工作；
2.基层：水泥砂浆地面（其他工种完成）；
3.综合考虑:地毯卡条、超高降效等费用；', 'm2', 34.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-05', '专业班组', '地面石材晶面处理', '1.工作内容：包含地面晶面处理施工所需的场地清理、填缝、细磨、精磨、抛光、防水、防污、晶面处理等一切工作（常规施工）；
2.综合考虑:石材翻新打磨、保养剂抛磨、防水防污、清洁表面、超高降效等费用；', 'm2', 48.0, '包工包料');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-06', '专业班组', '楼地面-美缝', '1.工作内容：包含完成美缝所需的一切工作；
2.嵌缝材料种类:专用美缝剂（符合设计要求）；
3.饰面材料规格:综合考虑；
4.综合考虑:清理缝隙中污垢、缝两边贴上美纹纸、超高降效等费用；', 'm2', 16.0, '包工包料');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-07', '专业班组', '楼板隔音垫', '1.工作内容：包含完成楼板隔音垫所需的一切工作；
2.隔音材料种类及规格:3厚聚氨酯橡胶隔声垫；
3.结合层种类:专用粘贴剂；
4.综合考虑:基层清理和平整、搭接宽度、超高施工降效等费用；', 'm2', 30.0, '包工包料');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-08', '专业班组', '地面隔声涂料', '1.工作内容：包含完成地面隔声涂料所需的一切工作；
2.面层材料规格、品种:3mm厚隔声涂料；
3.基层处理:专用界面剂；
4.综合考虑:基层打磨、分层涂刷、镘刀刮面、超高降效等费用；', 'm2', 25.08, '包工包料');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-09', '专业班组', '环氧树脂地面（地下停车场）', '1.工作内容：完成地面环氧地坪漆所需的材料运输、基层处理、地面环氧地坪漆施工等一切工作；
2.面层材料规格、品种:3mm厚环氧地坪漆【按实】；
3.基层处理:专用界面剂；
4.综合考虑:基层打磨、分层涂刷、镘刀刮面、超高降效等费用；', 'm2', 19.55, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-010', '专业班组', '墙面石材晶面处理', '1.工作内容：包含墙面晶面处理施工所需的场地清理、填缝、细磨、精磨、抛光、防水、防污、晶面处理等一切工作（常规施工）；
2.综合考虑:石材翻新打磨、保养剂抛磨、防水防污、清洁表面、超高降效等费用；', 'm2', 65.0, '包工包料');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-011', '专业班组', '墙面-美缝', '1.工作内容：包含完成美缝所需的一切工作；
2.嵌缝材料种类:专用美缝剂（符合设计要求）；
3.饰面材料规格:综合考虑；
4.综合考虑:清理缝隙中污垢、缝两边贴上美纹纸、超高降效等费用；', 'm2', 16.0, '包工包料');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-012', '专业班组', '墙面-铝塑板（常规）', '1.工作内容：完成墙面铝塑板所需的材料运输、基层处理、必要的板材现场加工、开孔、安装等一切工作；
2.其他工作：专业分包配合材料下单；
3.弧形面/零星项目人工费按1.1系数计算
4.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 51.2, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-013', '专业班组', '轻质隔墙', '1.工作内容：完成墙面轻质隔墙所需的材料运输、基层处理、必要的板材现场加工、开孔、安装等一切工作；
3.规格：50mm厚
2.其他工作：专业分包配合材料下单；
4.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 36.8, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-014', '专业班组', '轻质隔墙', '1.工作内容：完成墙面轻质隔墙所需的材料运输、基层处理、必要的板材现场加工、开孔、安装等一切工作；
3.规格：100mm厚
2.其他工作：专业分包配合材料下单；
4.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 40.48, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-015', '专业班组', '轻质隔墙', '1.工作内容：完成墙面轻质隔墙所需的材料运输、基层处理、必要的板材现场加工、开孔、安装等一切工作；
3.规格：200mm厚
2.其他工作：专业分包配合材料下单；
4.综合考虑:材料下单、基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 44.16, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-016', '专业班组', '天花饰面-铝扣板天花/矿棉板/亚克力板', '1.工作内容：完成铝扣板天花所需的材料运输、龙骨基层定位、安装、校平、扣件、收边条、隔音处理、扣板安装等一切工作；
天棚类型:铝扣板/亚克力吊顶
2.面层材料品种、规格:铝扣板/亚克力
3.龙骨材料种类、规格:轻钢龙骨、间距符合图纸要求
4.吊顶形式、吊杆规格、高度:符合设计及施工要求
5.综合考虑:金属收边条、固定件、密封填缝、超高降效等费用', 'm2', 43.7, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-017', '专业班组', '天花饰面-铝合金格栅吊顶', '1.工作内容：完成铝合金格栅吊顶所需的材料运输、板材切割加工、安装等一切工作；
2.材料规格：铝塑板天花；
3.需配合其他专业单位（消防、空调、机电）定位开孔；
4.综合考虑:材料下单、基层处理、固定边框、安装部位及方式、密缝收口、超高降效等费用；', 'm2', 48.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-018', '专业班组', '天棚透光膜饰面', '1.工作内容：完成天棚透光膜饰面所需的材料运输、金属材料局部切割加工、安装等一切工作；
2.天棚类型:天棚透光膜饰面；
3.面层材料品种、规格:透光膜；
4.综合考虑:基层处理、固定边框、安装部位及方式、密缝收口、超高降效等费用；', 'm2', 58.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-019', '专业班组', '天花饰面-GRG饰面', '1.工作内容：完成安装GRG饰面所需材料运输、板材切割加工、开孔、防腐处理等一切工作；
2.需配合其他专业单位（消防、空调、机电）定位开孔；
3.面层材料种类、规格:GRG饰面
4.综合考虑:基层类型、钉贴方式、封边填缝、超高降效等费用；', 'm2', 68.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('各专业班组', 'ZY-020', '专业班组', '卫生间成品隔断', '1.隔断材料种类、规格:抗倍特成品隔断【按实】；
2.综合考虑:隔断门、脚座、五金配件、超高降效等费用；', 'm2', 36.8, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'ZY-01', '架子工
（专业分包）', '满堂红脚手架', '1.工作内容：完成满堂红脚手架所需的设计方案、现场放线定位、根据方案和规范要求搭设扣件式脚手架、操作平台、铺板等一切内容
2.工程量按长宽高以m3计算；', 'm3', 30.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'ZY-02', '架子工
（专业分包）', '活动脚手架', '1.工作内容：完成活动脚手架所需的设计方案、现场放线定位、根据方案和规范要求搭设扣件式脚手架、操作平台、铺板等一切内容', 'm2', 6.92, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'ZY-03', '专业班组', '开荒保洁', '1.含一次粗开荒，需满足甲方验收并移交业主的标准:
2.工程量按装修面积计算:', 'm2', 6.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'ZY-04', '专业班组', '楼地面成品保护膜', '1.成品保护部位:楼地面
2.成品保护材料:PVC保护膜、编织布等【自填】
3.综合考虑:清扫表面、铺设及拆除、超高施工降效等费用', 'm2', 1.74, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'ZY-05', '专业班组', '楼地面成品保护板', '1.成品保护部位:楼地面
1.成品保护材料:5mm胶合板【自填】
2.综合考虑:清扫表面、铺设及拆除、超高施工降效等费用', 'm2', 3.05, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'ZY-06', '专业班组', '楼梯面成品保护膜', '1.成品保护部位:楼梯、台阶
2.成品保护材料:PVC保护膜、编织布等【自填】
2.综合考虑:清扫表面、铺设及拆除、超高施工降效等费用', 'm2', 2.35, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'ZY-07', '专业班组', '楼梯面成品保护板', '1.成品保护部位:楼梯、台阶
2.成品保护材料:5mm胶合板【自填】
3.综合考虑:清扫表面、铺设及拆除、超高施工降效等费用', 'm2', 3.46, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'ZY-08', '专业班组', '墙柱面成品保护膜', '1.成品保护部位:墙面、柱面
2.成品保护材料:PVC保护膜、编织布等【自填】
2.综合考虑:清扫表面、铺设及拆除、超高施工降效等费用', 'm2', 2.86, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'ZY-09', '专业班组', '墙柱面成品保护板', '1.成品保护部位:墙柱面
1.成品保护材料:5mm胶合板【自填】
2.综合考虑:清扫表面、铺设及拆除、超高施工降效等费用', 'm2', 3.74, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'ZY-010', '专业班组', '装饰墙成品保护板', '1.成品保护部位:装饰墙面、柱面
1.成品保护材料:5mm胶合板
3.成品保护龙骨:木龙骨
4.综合考虑:清扫表面、铺设及拆除、超高施工降效等费用', 'm2', 11.93, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'ZY-011', '专业班组', '栏杆成品保护膜', '1.成品保护材料:编织布
2.栏杆高度:1200m以内
2.综合考虑:清扫表面、铺设方式、超高施工降效等费用', 'm', 2.21, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'ZY-012', '专业班组', '成品保护 胶合板护角', '1.成品保护材料:9mm胶合板
2.成品保护龙骨:木龙骨
3.护角宽度:200×200mm
4.综合考虑:清扫表面、铺设方式、超高施工降效等费用', 'm', 1.83, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-01', '拆除班组', '砖砌体拆除', '1.拆除类型:砖砌体；
2.综合考虑:拆除方式、拆除部位、废渣堆放等费用；', 'm3', 124.73, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-02', '拆除班组', '混凝土构件拆除', '1.拆除类型:混凝土构件；
2.综合考虑:拆除部位、废渣堆放等费用；', 'm3', 207.89, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-03', '拆除班组', '钢筋混凝土构件体拆除', '1.拆除类型:钢筋混凝土构件；
2.综合考虑:拆除方式、废渣堆放等费用；', 'm3', 277.06, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-04', '拆除班组', '拆除地面找平层', '1.拆除类型:砂浆面层或找平层；
2.综合考虑:材料厚度、拆除方式、基层清洁、废渣堆放等费用；', 'm2', 10.96, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-05', '拆除班组', '拆除块料楼地面', '1.拆除类型:瓷砖、石材等块料；
2.综合考虑:拆除方式、基层清洁、废渣堆放等费用；', 'm2', 22.4, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-06', '拆除班组', '拆除木地板', '1.拆除类型:复合木地板、实木地板等；
2.综合考虑:拆除龙骨、拆除方式、基层清洁、废渣堆放等费用；', 'm2', 9.56, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-07', '拆除班组', '拆除踢脚线、装饰线', '1.拆除类型:金属踢脚、木踢脚线、装饰线等；
2.综合考虑:拆除方式、规格尺寸、基层清洁、废渣堆放等费用；', 'm', 1.78, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-08', '拆除班组', '拆除墙面找平层', '1.拆除类型:砂浆面层或找平层；
2.综合考虑:材料厚度、拆除方式、基层清洁、废渣堆放等费用；', 'm2', 11.43, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-09', '拆除班组', '拆除镶贴块料墙面', '1.拆除类型:瓷砖、石材等块料
2.综合考虑:拆除方式、基层清洁、废渣堆放等费用', 'm2', 21.08, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-010', '拆除班组', '拆除干挂块料墙面', '1.拆除类型:瓷砖、石材等块料；
2.综合考虑:拆除方式、龙骨拆除及回收、基层清洁、废渣堆放等费用；', 'm2', 18.73, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-011', '拆除班组', '拆除柔性防水', '1.拆除类型:防水卷材；
2.综合考虑:墙面/地面、拆除方式、基层清洁、废渣堆放等费用；', 'm2', 7.47, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-012', '拆除班组', '拆除装饰板墙面', '1.拆除方式:拆除装饰墙面；
2.拆除类型:金属饰面、木饰面、玻璃饰面等；
3.综合考虑:拆除方式、龙骨拆除及回收、基层清洁、废渣堆放等费用；', 'm2', 12.74, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-013', '拆除班组', '拆除隔墙/隔墙', '1.拆除方式:破坏性拆除装饰隔墙（含龙骨）；
2.拆除类型:金属饰面、木饰面、玻璃饰面等；
3.综合考虑:拆除方式、基层清洁、废渣堆放等费用；', 'm2', 20.01, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-014', '拆除班组', '铲除乳胶漆饰面', '1.拆除类型:乳胶漆及腻子；
2.综合考虑:墙面/天棚、铲除方式、基层清洁、废渣堆放等费用；', 'm2', 6.72, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-015', '拆除班组', '拆除天棚抹灰', '1.拆除类型:砂浆面层或找平层；
2.综合考虑:材料厚度、拆除方式、基层清洁、废渣堆放等费用；', 'm2', 11.85, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-016', '拆除班组', '拆除天棚吊顶', '1.拆除类型:破坏性拆除装饰墙面；
2.天棚类型:金属饰面、木饰面、石膏饰面等；
3.综合考虑:拆除方式、基层清洁、龙骨拆除及回收、废渣堆放等费用；', 'm2', 12.19, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-017', '拆除班组', '拆除木质门窗', '1.拆除类型:木质门窗；
2.综合考虑:规格尺寸、拆除方式、基层清洁、废渣堆放等费用；', 'm2', 17.77, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-018', '拆除班组', '拆除金属门窗', '1.拆除类型:金属门窗；
2.综合考虑:规格尺寸、拆除方式、基层清洁、废渣堆放等费用；', 'm2', 18.54, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-019', '拆除班组', '拆除金属栏杆', '1.拆除类型:金属栏杆（含扶手、立杆）；
2.综合考虑:规格尺寸、拆除方式、基层清洁、废渣堆放等费用；', 'm', 28.56, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-020', '拆除班组', '拆除金属扶手', '1.拆除类型:金属扶手、立杆；
2.综合考虑:规格尺寸、拆除方式、基层清洁、废渣堆放等费用；', 'm', 4.36, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-021', '拆除班组', '拆除家居柜', '1.拆除类型:家居柜；
2.综合考虑:柜体深度、拆除方式、基层清洁、废渣堆放等费用；', 'm2', 26.58, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-022', '拆除班组', '拆除灯槽、窗帘盒', '1.拆除类型:灯槽、窗帘盒；
2.综合考虑:规格尺寸、窗帘杆、拆除方式、基层清洁、废渣堆放等费用；', 'm', 7.68, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-023', '拆除班组', '砌体开孔 100mm以内', '1.打洞部位材质:砖砌体
2.洞口直径或边长:100mm（含）以内
3.综合考虑:开孔方式及部位、开孔形状及深度、洞口清洁、废渣堆放等费用', '个', 13.65, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-024', '拆除班组', '砌体开孔 200mm以内', '1.打洞部位材质:砖砌体
2.洞口直径或边长:200mm（含）以内
3.综合考虑:开孔方式及部位、开孔形状及深度、洞口清洁、废渣堆放等费用', '个', 18.9, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-025', '拆除班组', '砌体开孔 300mm以内', '1.打洞部位材质:砖砌体
2.洞口直径或边长:300mm（含）以内
3.综合考虑:开孔方式及部位、开孔形状及深度、洞口清洁、废渣堆放等费用', '个', 23.1, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-026', '拆除班组', '混凝土开孔 100mm以内', '1.打洞部位材质:混凝土
2.洞口直径或边长:100mm（含）以内
3.综合考虑:开孔方式及部位、开孔形状及深度、洞口清洁、废渣堆放等费用', '个', 30.03, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-027', '拆除班组', '混凝土开孔 200mm以内', '1.打洞部位材质:混凝土
2.洞口直径或边长:200mm（含）以内
3.综合考虑:开孔方式及部位、开孔形状及深度、洞口清洁、废渣堆放等费用', '个', 41.58, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-028', '拆除班组', '混凝土开孔 300mm以内', '1.打洞部位材质:混凝土
2.洞口直径或边长:300mm（含）以内
3.综合考虑:开孔方式及部位、开孔形状及深度、洞口清洁、废渣堆放等费用', '个', 50.82, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-029', '拆除班组', '装饰墙开孔 100mm以内', '1.打洞部位材质:石材、瓷砖、饰面板等
2.洞口直径或边长:100mm（含）以内
3.综合考虑:开孔方式及部位、开孔形状及深度、洞口清洁、废渣堆放等费用', '个', 8.19, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-030', '拆除班组', '装饰墙开孔 200mm以内', '1.打洞部位材质:石材、瓷砖、饰面板等
2.洞口直径或边长:200mm（含）以内
3.综合考虑:开孔方式及部位、开孔形状及深度、洞口清洁、废渣堆放等费用', '个', 11.34, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-031', '拆除班组', '装饰墙开孔 400mm以内', '1.打洞部位材质:石材、瓷砖、饰面板等
2.洞口直径或边长:300mm（含）以内
3.综合考虑:开孔方式及部位、开孔形状及深度、洞口清洁、废渣堆放等费用', '个', 13.86, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-032', '拆除班组', '建筑垃圾外运 3km内', '1.土壤类别:拆除废料、建筑垃圾、生活垃圾等
2.挖运方式:人工装车、自卸汽车运输
3.运距:3km
4.综合考虑:机械类型、场内运距等费用', 'm3', 43.69, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('其他班组', 'CC-033', '拆除班组', '建筑垃圾外运 每增加1km', '1.土壤类别:拆除废料、生活垃圾、建筑包装
2.挖运方式:人工装车、自卸汽车运输
3.增加运距:1km
4.综合考虑:机械类型、场内运距等费用', 'm3', 3.11, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-01', '幕墙工', '外墙肌理涂料', '1.工作内容：外墙肌理涂料；
2.材料规格：外墙涂料，符合设计图纸、行业规范及招标技术规格书要求，依据设计图示尺寸，按投影面积计算；
3.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 40.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-02', '幕墙工', '外墙真石漆', '1.工作内容：外墙真石漆；
2.材料规格：外墙涂料，符合设计图纸、行业规范及招标技术规格书要求，依据设计图示尺寸，按投影面积计算；
3.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 40.96, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-03', '幕墙工', '外墙砖', '1.工作内容：外墙砖；
2.材料规格：外墙砖，符合设计图纸、行业规范及招标技术规格书要求，依据设计图示尺寸，按投影面积计算；
3.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 50.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-04', '幕墙工', '预制陶土砖幕墙', '1.工作内容：预制陶土砖幕墙安装；
2.材料规格：预制陶土砖，形状详见设计图纸，符合设计图纸、行业规范及招标技术规格书要求，依据设计图示尺寸，按外框面积计算；
3.连接方式：槽钢连接件、不锈钢螺栓等；
4.骨架种类、规格、间距:高精级铝合金型材，铝合金立柱、T型铝合金托板、不锈钢全螺纹圆管等，不锈钢套筒、不锈钢配件、尼龙垫块等、规格及间距详见设计图纸；
5.紧固件及锚栓:槽钢连接件、不锈钢螺栓等，详见设计图纸；
6.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 170.39, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-05', '幕墙工', '石材幕墙', '1.工作内容：石材幕墙安装；
2.材料规格：石材幕墙，形状详见设计图纸，符合设计图纸、行业规范及招标技术规格书要求，依据设计图示尺寸，按外框面积计算；
3.连接方式：采用干挂系统（不锈钢背栓系统）；
4.骨架种类、规格、间距:热浸镀锌钢型材等、规格及间距详见设计图纸；
5.紧固件及锚栓:槽钢连接件、不锈钢螺栓等，详见设计图纸；
6.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 243.87, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-06', '幕墙工', '带骨架玻璃幕墙', '1.工作内容：带骨架玻璃幕墙/明框玻璃幕墙安装；
2.材料规格：带骨架玻璃幕墙/明框玻璃幕墙，钢化中空玻璃,材质及规格详见设计图纸，颜色符合业主及设计要求，依据设计图示尺寸，按外框面积计算；
3.骨架种类、规格、间距:高精级铝合金型材（表面氟碳喷涂）、国产优质钢型材（氟碳喷涂）等，铝合金立柱、铝合金横梁，规格及间距详见设计图纸；
4.保温及防火材料:200厚防火岩棉、50mm厚保温岩棉、1.5mm厚镀锌钢板等，详见设计图纸；
5.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
7.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
8.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 178.21, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-07', '幕墙工', '带骨架玻璃幕墙（带背衬板）', '1.工作内容：带骨架玻璃幕墙/明框玻璃幕墙（带背衬板）安装；
2.材料规格：带骨架玻璃幕墙/明框玻璃幕墙（带背衬板），钢化中空玻璃,材质及规格详见设计图纸，颜色符合业主及设计要求，依据设计图示尺寸，按外框面积计算；
3.骨架种类、规格、间距:高精级铝合金型材（表面氟碳喷涂）、国产优质钢型材（氟碳喷涂）等，铝合金立柱、铝合金横梁，规格及间距详见设计图纸；
4.保温及防火材料:200厚防火岩棉、50mm厚保温岩棉、1.5mm厚镀锌钢板等，详见设计图纸；
5.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
7.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
8.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 178.21, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-08', '幕墙工', '全玻(无框玻璃)幕墙', '1.工作内容：全玻(无框玻璃)幕墙安装；
2.材料规格：全玻(无框玻璃)幕墙，钢化中空玻璃,材质及规格详见设计图纸，颜色符合业主及设计要求，依据设计图示尺寸，按外框面积计算；
3.骨架种类、规格、间距:高精级铝合金型材（表面氟碳喷涂）、国产优质钢型材（氟碳喷涂）等，铝合金立柱、铝合金横梁，规格及间距详见设计图纸；
4.保温及防火材料:200厚防火岩棉、50mm厚保温岩棉、1.5mm厚镀锌钢板等，详见设计图纸；
5.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
7.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
8.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 178.21, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-09', '幕墙工', '铝板幕墙
（带铝背板）', '1.工作内容：铝板幕墙（带铝背板）安装；
2.材料规格：明框铝板幕墙（带铝背板），氟碳喷涂铝板(铜色)，规格及颜色详见设计图纸，依据设计图示尺寸，按外框面积计算；
3.骨架种类、规格、间距:高精级铝合金型材、国产优质钢型材等，铝合金立柱、铝合金横梁、镀锌钢芯，规格及间距满足设计图纸要求；
4.保温及防火材料:满足设计图纸要求；
5.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
7.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
8.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 175.16, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-010', '幕墙工', '造型铝板幕墙
（带铝背板）', '1.工作内容：造型铝板幕墙（带铝背板）安装；
2.材料规格：造型铝板幕墙（带铝背板），氟碳喷涂铝板(铜色)，规格及颜色详见设计图纸，依据设计图示尺寸，铝板展开面积计算；
3.骨架种类、规格、间距:高精级铝合金型材、国产优质钢型材等，铝合金立柱、铝合金横梁、镀锌钢芯，规格及间距满足设计图纸要求；
4.保温及防火材料:满足设计图纸要求；
5.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
7.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
8.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 192.28, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-011', '幕墙工', '造型铝板幕墙', '1.工作内容：造型铝板幕墙安装；
2.材料规格：造型铝板幕墙，氟碳喷涂铝板(铜色)，规格及颜色详见设计图纸，依据设计图示尺寸，铝板展开面积计算；
3.骨架种类、规格、间距:高精级铝合金型材、国产优质钢型材等，铝合金立柱、铝合金横梁、镀锌钢芯，规格及间距满足设计图纸要求；
4.保温及防火材料:满足设计图纸要求；
5.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
7.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
8.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 192.28, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-012', '幕墙工', '铝板饰面包边', '1.工作内容：铝板饰面包边安装；
2.材料规格：铝板饰面包边，氟碳喷涂铝板，规格及颜色详见设计图纸，依据设计图示尺寸，铝板展开面积计算；
3.骨架种类、规格、间距:国产优质钢型材等，镀锌角钢及钢通等、规格及间距详见设计图纸；
4.保温及防火材料:满足设计图纸要求；
5.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
7.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
8.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 165.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-013', '幕墙工', '铝合金型材装饰线条', '1.工作内容：铝合金型材装饰线条安装；
2.材料规格：铝合金装饰扣盖，100mm以内；
3.骨架种类、规格、间距:国产优质钢型材（热浸锌防腐处理）等，镀锌角钢及钢通等、规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
5.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
6.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 30.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-014', '幕墙工', '铝合金型材装饰线条', '1.工作内容：铝合金型材装饰线条安装；
2.材料规格：铝合金装饰扣盖，150mm以内；
3.骨架种类、规格、间距:国产优质钢型材（热浸锌防腐处理）等，镀锌角钢及钢通等、规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
5.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
6.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 30.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-015', '幕墙工', '铝合金型材装饰线条', '1.工作内容：铝合金型材装饰线条安装；
2.材料规格：铝合金装饰扣盖，200mm以内；
3.骨架种类、规格、间距:国产优质钢型材（热浸锌防腐处理）等，镀锌角钢及钢通等、规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
5.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
6.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 43.72, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-016', '幕墙工', '铝板灯槽线条', '1.工作内容：铝板灯槽线条安装；
2.材料规格：铝合金装饰扣盖，100mm以内；
3.骨架种类、规格、间距:国产优质钢型材（热浸锌防腐处理）等，镀锌角钢及钢通等、规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
5.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
6.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 32.79, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-017', '幕墙工', '陶板线条', '1.工作内容：陶板线条安装；
2.材料规格：陶板线条，100mm以内；
3.骨架种类、规格、间距:国产优质钢型材（热浸锌防腐处理）等，镀锌角钢及钢通等、规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
5.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
6.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 43.72, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-018', '幕墙工', '陶板线条', '1.工作内容：陶板线条安装；
2.材料规格：陶板线条，100-200mm以内；
3.骨架种类、规格、间距:国产优质钢型材（热浸锌防腐处理）等，镀锌角钢及钢通等、规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
5.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
6.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 53.38, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-019', '幕墙工', '陶板线条', '1.工作内容：陶板线条安装；
2.材料规格：陶板线条，200-300mm以内；
3.骨架种类、规格、间距:国产优质钢型材（热浸锌防腐处理）等，镀锌角钢及钢通等、规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
5.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
6.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 80.08, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-020', '幕墙工', '幕墙钢架', '1.工作内容：幕墙钢架安装；
2.材料规格：镀锌型钢，按设计要求综合考虑规格、种类；
3.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
4.预埋件：镀锌预埋件；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'T', 4250.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-021', '幕墙工', '预埋件', '1.工作内容：幕墙预埋件安装；
2.材料规格：镀锌型钢，按设计要求综合考虑规格、种类；
3.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
4.预埋件：镀锌预埋件；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'T', 5600.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-022', '幕墙工', '幕墙防火隔断', '1.工作内容：幕墙防火隔断安装；
2.材料规格：镀锌钢板，端部和拼接处防火密封胶密封、防火岩棉单面锡箔包裹填满；
3.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 75.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-023', '幕墙工', '钢支撑、钢拉条', '1.工作内容：钢支撑、钢拉条安装；
2.材料规格：Ф34不锈钢拉索、Ф68支撑杆、材质及规格详见设计图纸，颜色符合业主及设计要求，品牌要求详见幕墙技术说明书等；
3. 连接及连接件、收口处镀锌钢板、封堵、面层固定、扣盖、密封、嵌缝、塞口、螺栓、锚栓、五金配件、防雷处理等，详见图纸要求及做法综合考虑详见设计图纸；
4.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 210.37, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-024', '幕墙工', '屋顶蜘蛛人吊挂件（底座）', '1.工作内容：屋顶蜘蛛人吊挂件（底座）安装；
2.材料规格：镀锌方通，10厚镀锌钢板，具体详图纸；
3.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', '个', 98.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-025', '幕墙工', '屋顶蜘蛛人吊挂件（插杆）', '1.工作内容：屋顶蜘蛛人吊挂件（插杆）安装；
2.材料规格：镀锌方通，10厚镀锌钢板，具体详图纸；
3.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', '个', 23.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-026', '幕墙工', '幕墙竖向伸缩缝', '1.工作内容：幕墙竖向伸缩缝安装；
2.材料规格：1.5mm泛水铝板，150mm宽，国产优质高精级铝合金型材，密封胶条、结构胶、螺钉等一切为完成本项目必需的各种材料；，具体详图纸；
3.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 50.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-027', '幕墙工', '幕墙横向伸缩缝', '1.工作内容：幕墙横向伸缩缝安装；
2.材料规格：铝板，500mm宽，国产优质高精级铝合金型材，2mm防水胶条（通长）,80*5镀锌钢通,铝合金角码、密封胶条、结构胶、螺钉等一切为完成本项目必需的各种材料；
3.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 50.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-028', '幕墙工', '防火采光系统（天棚/墙身）', '1.工作内容：防火采光系统（天棚、墙身）安装；
2.材料规格：防火夹胶中空玻璃（耐火完整时限≥1h），氟碳喷涂铝板包边，高精级铝合金扣盖（氟碳喷涂），钢压板（氟碳喷涂），规格及颜色详见设计图纸，按屋面斜面积计算；
3.骨架种类、规格、间距:国产优质钢型材等，镀锌钢通等规格及间距详见设计图纸；
4.保温及防火材料:满足设计图纸要求；
5.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
6.预埋件：镀锌预埋件；
7.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
8.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 193.31, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-029', '幕墙工', '不锈钢排水槽', '1.工作内容：不锈钢排水槽安装；
2.材料规格：槽内高度：200mm以内，不锈钢（304材质），规格及颜色详见设计图纸；
3.龙骨：国产优质镀锌型钢，规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 140.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-030', '幕墙工', '集水沟', '1.工作内容：集水沟安装；
2.材料规格：不锈钢成品篦子，2mm厚不锈钢水槽，分隔详见图纸，具体设计参数详图纸要求；
3.龙骨：国产优质镀锌型钢，规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 140.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-031', '幕墙工', '镂空铝板', '1.工作内容：镂空铝板安装；
2.材料规格：氟碳喷涂穿孔铝板，规格及形状详见设计图纸，规格及形状设计图纸，依据设计图示尺寸，按外框投影面积计算；
3.骨架种类、规格、间距:国产优质钢型材等，镀锌钢通等规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 150.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-032', '幕墙工', '铝质窗花', '1.工作内容：铝质窗花安装；
2.材料规格：氟碳喷涂铝合金方通窗花，规格及图案详见设计图纸，规格及形状设计图纸，依据设计图示尺寸，按外框投影面积计算；
3.骨架种类、规格、间距:国产优质钢型材等，镀锌钢通等规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 165.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-033', '幕墙工', '铝百叶
（带背板）', '1.工作内容：铝百叶（带背板）安装；
2.材料规格：铝合金百叶，规格及形状设计图纸，背衬铝板，依据设计图示尺寸，按外框投影面积计算；
3.骨架种类、规格、间距:国产优质钢型材等，镀锌钢通等规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 175.16, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-034', '幕墙工', '铝百叶（带防鸟网）', '1.工作内容：铝百叶（带防鸟网）安装；
2.材料规格：铝合金百叶，规格及形状设计图纸，背衬不锈钢防鸟网，依据设计图示尺寸，按外框投影面积计算；
3.骨架种类、规格、间距:国产优质钢型材等，镀锌钢通等规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 175.16, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-035', '幕墙工', '铝百叶（铝骨架、带防鸟网）', '1.工作内容：铝百叶（铝骨架、带防鸟网）安装；
2.材料规格：铝合金百叶，规格及形状设计图纸，背衬不锈钢防鸟网，依据设计图示尺寸，按外框投影面积计算；
3.骨架种类、规格、间距:国产优质钢型材等，镀锌钢通等规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 175.16, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-036', '幕墙工', '铝合金格栅', '1.工作内容：铝合金格栅安装；
2.材料规格：铝合金格栅@100mm以内，规格及颜色详见设计图纸；
3.骨架种类、规格、间距:国产优质镀锌型钢，工字钢及方钢等规格及间距详见设计图纸；
4.连接方式：10厚镀锌钢板加强肋、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:塞口材料种类:详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 175.16, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-037', '幕墙工', '铝板店招', '1.工作内容：铝板店招安装；
2.材料规格：内框深度200mm，氟碳喷涂铝板，规格及颜色详见设计图纸，依据设计图示尺寸，按外框立面投影面积计算；
3.骨架种类、规格、间距:国产优质钢型材等，镀锌钢通等规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 175.16, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-038', '幕墙工', '铝板店招', '1.工作内容：铝板店招安装；
2.材料规格：内框深度120mm内，氟碳喷涂铝板，规格及颜色详见设计图纸，依据设计图示尺寸，按外框立面投影面积计算；
3.骨架种类、规格、间距:国产优质钢型材等，镀锌钢通等规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 175.16, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-039', '幕墙工', '悬挑铝板雨棚', '1.工作内容：悬挑铝板雨棚安装；
2.材料规格：雨棚厚度1540mm，依据设计图示尺寸，按水平投影面积计算；
3.骨架种类、规格、间距:国产优质钢型材等，镀锌钢通等规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 351.94, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-040', '幕墙工', '铝板雨棚', '1.工作内容：铝板雨棚安装；
2.材料规格：雨棚厚度80~100mm，氟碳喷涂铝板，规格及形状设计图纸，依据设计图示尺寸，按水平投影面积计算；
3.骨架种类、规格、间距:国产优质钢型材等，镀锌钢通等规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 175.97, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-041', '幕墙工', '玻璃雨棚', '1.工作内容：玻璃雨棚安装；
2.材料规格：钢化夹胶玻璃，规格及颜色详见设计图纸，按屋面斜面积计算；
3.骨架种类、规格、间距:国产优质钢型材等，镀锌钢通等规格及间距详见设计图纸；
4.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
5.预埋件：镀锌预埋件；
6.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
7.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 146.82, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-042', '幕墙工', '玻璃栏杆', '1.工作内容：玻璃栏杆安装；
2.材料规格：900~1150mm，钢化夹胶玻璃，异形不锈钢扶手，矩形不锈钢立柱，高精级铝合金扣盖，2mm厚不锈钢压板，规格及颜色详见设计图纸，依据设计图示尺寸，按栏杆中心线长度计算；
3.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
4.预埋件：镀锌预埋件；
5.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
6.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 101.92, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-043', '幕墙工', '铝合金栏杆', '1.工作内容：铝合金栏杆安装；
2.材料规格：900~1150mm，铝型材，异形不锈钢扶手，矩形不锈钢立柱，高精级铝合金扣盖，2mm厚不锈钢压板，规格及颜色详见设计图纸，依据设计图示尺寸，按栏杆中心线长度计算；
3.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
4.预埋件：镀锌预埋件；
5.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
6.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 133.49, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-044', '幕墙工', '不锈钢扶手', '1.工作内容：不锈钢扶手安装；
2.材料规格：15mm厚不锈钢板，具体详图纸，依据设计图示尺寸，按延长米计算；
3.连接方式：镀锌钢连接件、不锈钢螺栓等，详见设计图纸；
4.预埋件：镀锌预埋件；
5.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
6.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm', 28.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-045', '幕墙工', '玻璃幕墙手动开启窗', '1.工作内容：玻璃幕墙开启窗（排烟窗、上悬窗手动开启装置）安装；
2.材料规格：玻璃幕墙开启窗（普通开启窗），符合设计图纸、行业规范及招标技术规格书要求，依据设计图示尺寸，按外框面积计算；
3.五金配件：锁点、铰链、风撑、执手、限位器等安装；
4.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 150.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-046', '幕墙工', '玻璃幕墙电动开启窗', '1.工作内容：玻璃幕墙开启窗（排烟窗、上悬窗电动开启装置）安装；
2.材料规格：玻璃幕墙开启窗（普通开启窗），符合设计图纸、行业规范及招标技术规格书要求，依据设计图示尺寸，按外框面积计算；
3.五金配件：锁点、铰链、风撑、执手、限位器等安装
4.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 178.21, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-047', '幕墙工', '金属格栅窗', '1.工作内容：金属格栅窗安装；
2.材料规格：金属格栅窗，符合设计图纸、行业规范及招标技术规格书要求，依据设计图示尺寸，按外框面积计算；
3.五金配件：锁点、铰链、风撑、执手、限位器等安装；
4.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 178.21, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-048', '幕墙工', '普通铝合金窗', '1.工作内容：普通铝合金窗安装；
2.材料规格：普通铝合金窗，符合设计图纸、行业规范及招标技术规格书要求，依据设计图示尺寸，按外框面积计算；
3.五金配件：锁点、铰链、风撑、执手、限位器等安装
4.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 49.07, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-049', '幕墙工', '铝合金推拉门', '1.工作内容：铝合金推拉门安装；
2.材料规格：铝合金推拉门，详见图纸要求；
3.五金配件：锁点、铰链、风撑、执手、限位器等安装；
4.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 62.79, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-050', '幕墙工', '铝合金平开门', '1.工作内容：铝合金平开门安装；
2.材料规格：铝合金平开门，详见图纸要求；
3.五金配件：锁点、铰链、风撑、执手、限位器等安装；
4.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 68.82, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-051', '幕墙工', '铝单板饰面地弹门', '1.工作内容：铝单板饰面地弹门安装；
2.材料规格：铝单板饰面地弹门，氟碳漆穿孔铝单板、氟碳漆穿孔铝单板、防火保温岩棉、高精级铝合金型材龙骨及连接件；
3.五金配件：锁点、铰链、风撑、执手、限位器等安装；
4.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 135.24, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-052', '幕墙工', '铝合金玻璃地弹门', '1.工作内容：铝合金玻璃地弹门安装；
2.材料规格：钢化中空玻璃，高精级铝合金型材门框等；
3.五金配件：锁点、铰链、风撑、执手、限位器等安装；
4.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 135.24, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-053', '幕墙工', '全玻地弹门', '1.工作内容：全玻地弹门安装；
2.材料规格：钢化中空玻璃，不锈钢板，骨架采用镀锌角钢、镀锌方管；底部采用铝合金型材槽，M12化学锚栓；规格如图所示等；
3.五金配件：锁点、铰链、风撑、执手、限位器等安装；
4.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 137.49, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-054', '幕墙工', '电动感应门', '1.工作内容：电动感应门安装；
2.材料规格：钢化中空玻璃，不锈钢板，骨架采用镀锌角钢、镀锌方管；底部采用铝合金型材槽，M12化学锚栓；规格如图所示等；
3.五金配件：锁点、铰链、风撑、执手、限位器等安装；
4.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 137.49, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('幕墙班组', 'MQ-055', '幕墙工', '旋转感应门', '1.工作内容：电动旋转门安装；
2.材料规格：钢化中空玻璃，不锈钢板，骨架采用镀锌角钢、镀锌方管；底部采用铝合金型材槽，M12化学锚栓；规格如图所示等；
3.五金配件：锁点、铰链、风撑、执手、限位器等安装；
4.嵌缝、塞口材料种类:泡沫棒、硅酮密封胶、三元乙丙胶条等，详见设计图纸；
5.综合考虑:基层清理、材料的场内（外）运输、预前加工、制作、安装、焊接、调正、收口、刷防锈漆（富锌漆）等、防雷系统连接、防火处理、清洗及成品保护、建筑物超高降效、场地条件、夜间施工、配合各专业工程交叉施工等增加费；', 'm2', 163.4, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-01', '水电工', '桥架/金属线槽(宽+高)≤50mm', '1.名称：桥架/金属线槽；
2.规格、型号：(宽+高)≤50mm 厚度综合考虑；
3.材质：不分材质，综合考虑；
4.桥架盖板安装，含接地跨接线安装，隔板、连接片、螺栓、弯头、变径、三通等', 'm', 8.89, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-02', '水电工', '桥架/金属线槽50mm＜(宽+高)≤80mm', '1.名称：桥架/金属线槽；
2.规格、型号：50mm＜(宽+高)≤80mm 厚度综合考虑；
3.材质：不分材质，综合考虑；
4.桥架盖板安装，含接地跨接线安装，隔板、连接片、螺栓、弯头、变径、三通等', 'm', 11.02, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-03', '水电工', '桥架/金属线槽80mm＜(宽+高)≤120mm', '1.名称：桥架/金属线槽
2.规格、型号：80mm＜(宽+高)≤120mm 厚度综合考虑；
3.材质：不分材质，综合考虑；
4.桥架盖板安装，含接地跨接线安装，隔板、连接片、螺栓、弯头、变径、三通等；', 'm', 14.58, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-04', '水电工', '桥架/金属线槽120mm＜(宽+高)≤150mm', '1.名称：桥架/金属线槽；
2.规格、型号：120mm＜(宽+高)≤150mm 厚度综合考虑；
3.材质：不分材质，综合考虑；
4.桥架盖板安装，含接地跨接线安装，隔板、连接片、螺栓、弯头、变径、三通等；', 'm', 26.43, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-05', '水电工', '桥架/金属线槽150mm＜(宽+高)≤300mm', '1.名称：桥架/金属线槽；
2.规格、型号：150mm＜(宽+高)≤300mm 厚度综合考虑；
3.材质：不分材质，综合考虑；
4.桥架盖板安装，含接地跨接线安装，隔板、连接片、螺栓、弯头、变径、三通等；', 'm', 26.43, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-06', '水电工', '桥架/金属线槽300mm＜(宽+高)≤400mm', '1.名称：桥架/金属线槽；
2.规格、型号：300mm＜(宽+高)≤400mm 厚度综合考虑；
3.材质：不分材质，综合考虑；
4.桥架盖板安装，含接地跨接线安装，隔板、连接片、螺栓、弯头、变径、三通等；', 'm', 32.7, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-07', '水电工', 'PVC管 DN15', '1.名称:塑料电线管；
2.规格型号:PC15；
3.敷设方式:综合考虑明、暗敷；
4.工作内容:测位、划线、锯管、套丝、煨弯、配管、接地、刷漆、接线盒、灯头盒等；
5.完成该项工作的其他一切未尽事宜。', 'm', 4.88, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-08', '水电工', 'PVC管 DN20', '1.名称:塑料电线管；
2.规格型号:PC20；
3.敷设方式:综合考虑明、暗敷；
4.工作内容:测位、划线、锯管、套丝、煨弯、配管、接地、刷漆、接线盒、灯头盒等；
5.完成该项工作的其他一切未尽事宜。', 'm', 5.92, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-09', '水电工', 'PVC管 DN25', '1.名称:塑料电线管；
2.规格型号:PC25；
3.敷设方式:综合考虑明、暗敷；
4.工作内容:测位、划线、锯管、套丝、煨弯、配管、接地、刷漆、接线盒、灯头盒等；
5.完成该项工作的其他一切未尽事宜。', 'm', 6.87, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-010', '水电工', 'PVC管 DN32', '1.名称:塑料电线管；
2.规格型号:PC32；
3.敷设方式:综合考虑明、暗敷；
4.工作内容:测位、划线、锯管、套丝、煨弯、配管、接地、刷漆、接线盒、灯头盒等；
5.完成该项工作的其他一切未尽事宜。', 'm', 8.43, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-011', '水电工', 'PVC管 DN40', '1.名称:塑料电线管；
2.规格型号:PC40；
3.敷设方式:综合考虑明、暗敷；
4.工作内容:测位、划线、锯管、套丝、煨弯、配管、接地、刷漆、接线盒、灯头盒等；
5.完成该项工作的其他一切未尽事宜。', 'm', 8.61, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-012', '水电工', 'PVC管 DN50', '1.名称:塑料电线管；
2.规格型号:PC50；
3.敷设方式:综合考虑明、暗敷；
4.工作内容:测位、划线、锯管、套丝、煨弯、配管、接地、刷漆、接线盒、灯头盒等；
5.完成该项工作的其他一切未尽事宜。', 'm', 9.78, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-013', '水电工', '镀锌电线管 DN15', '1.名称:镀锌电线管；
2.规格型号:DN15；
3.敷设方式:综合考虑明、暗敷；
4.工作内容:穿引线测位、划线、锯管、套丝、煨弯、配管、接地、刷漆、支架制安、接线盒、灯头盒等。
5.完成该项工作的其他一切未尽事宜。', 'm', 4.98, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-014', '水电工', '镀锌电线管 DN20', '1.名称:镀锌电线管；
2.规格型号:DN20；
3.敷设方式:综合考虑明、暗敷；
4.工作内容:穿引线测位、划线、锯管、套丝、煨弯、配管、接地、刷漆、支架制安、接线盒、灯头盒等。
5.完成该项工作的其他一切未尽事宜。', 'm', 7.2, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-015', '水电工', '镀锌电线管 DN25', '1.名称:镀锌电线管；
2.规格型号:DN25；
3.敷设方式:综合考虑明、暗敷；
4.工作内容:穿引线测位、划线、锯管、套丝、煨弯、配管、接地、刷漆、支架制安、接线盒、灯头盒等。
5.完成该项工作的其他一切未尽事宜。', 'm', 7.89, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-016', '水电工', '镀锌电线管 DN32', '1.名称:镀锌电线管；
2.规格型号:DN32；
3.敷设方式:综合考虑明、暗敷；
4.工作内容:穿引线测位、划线、锯管、套丝、煨弯、配管、接地、刷漆、支架制安、接线盒、灯头盒等。
5.完成该项工作的其他一切未尽事宜。', 'm', 8.15, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-017', '水电工', '镀锌电线管 DN40', '1.名称:镀锌电线管；
2.规格型号:DN40；
3.敷设方式:综合考虑明、暗敷；
4.工作内容:穿引线测位、划线、锯管、套丝、煨弯、配管、接地、刷漆、支架制安、接线盒、灯头盒等。
5.完成该项工作的其他一切未尽事宜。', 'm', 9.17, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-018', '水电工', '镀锌电线管 DN50', '1.名称:镀锌电线管；
2.规格型号:DN50；
3.敷设方式:综合考虑明、暗敷；
4.工作内容:穿引线测位、划线、锯管、套丝、煨弯、配管、接地、刷漆、支架制安、接线盒、灯头盒等。
5.完成该项工作的其他一切未尽事宜。', 'm', 10.42, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-019', '水电工', '金属软管 DN15', '1.名称:金属软管；
2.规格型号:DN15；
3.敷设方式:综合考虑；
4.每根管长:综合考虑；
5.工作内容:测位、接线、锯管、套丝、煨弯、配管、接地、刷漆、接线盒、灯头盒等。
6.完成该项工作的其他一切未尽事宜。', 'm', 5.32, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-020', '水电工', '金属软管 DN20', '1.名称:金属软管；
2.规格型号:DN20；
3.敷设方式:综合考虑；
4.每根管长:综合考虑；
5.工作内容:测位、接线、锯管、套丝、煨弯、配管、接地、刷漆、接线盒、灯头盒等。
6.完成该项工作的其他一切未尽事宜。', 'm', 5.6, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-021', '水电工', '金属软管 DN25', '1.名称:金属软管；
2.规格型号:DN25；
3.敷设方式:综合考虑；
4.每根管长:综合考虑；
5.工作内容:测位、接线、锯管、套丝、煨弯、配管、接地、刷漆、接线盒、灯头盒等。
6.完成该项工作的其他一切未尽事宜。', 'm', 5.78, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-022', '水电工', '金属软管 DN32', '1.名称:金属软管；
2.规格型号:DN32；
3.敷设方式:综合考虑；
4.每根管长:综合考虑；
5.工作内容:测位、接线、锯管、套丝、煨弯、配管、接地、刷漆、接线盒、灯头盒等。
6.完成该项工作的其他一切未尽事宜。', 'm', 6.1, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-023', '水电工', '电气配线ZR-BV-2.5', '1.配线形式:综合考虑；
2.规格型号:2.5mm2；
3.材质:铜芯 ；
4.工作内容:穿引线、扫管、涂滑石粉、穿线、编号、接焊包头。
5.完成该项工作的其他一切未尽事宜。', 'm', 0.99, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-024', '水电工', '电气配线ZR-BV-4', '1.配线形式:综合考虑；
2.规格型号:4mm2；
3.材质:铜芯 ；
4.工作内容:穿引线、扫管、涂滑石粉、穿线、编号、接焊包头。
5.完成该项工作的其他一切未尽事宜。', 'm', 0.86, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-025', '水电工', '电气配线ZR-BV-6', '1.配线形式:综合考虑；
2.规格型号:6mm2；
3.材质:铜芯 ；
4.工作内容:穿引线、扫管、涂滑石粉、穿线、编号、接焊包头。
5.完成该项工作的其他一切未尽事宜。', 'm', 0.86, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-026', '水电工', '电气配线ZR-BV-10', '1.配线形式:综合考虑；
2.规格型号:10mm2；
3.材质:铜芯 ；
4.工作内容:穿引线、扫管、涂滑石粉、穿线、编号、接焊包头。
5.完成该项工作的其他一切未尽事宜。', 'm', 1.17, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-027', '水电工', '网络线（5类）', '1.配线形式:综合考虑；
2.导线型号、规格:网络线（5类）；
3.其它:穿线、编号、焊压接线端子及相关配件安装；
4.线路测试及完成该项工作的其他一切未尽事宜。', 'm', 1.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-028', '水电工', '网络线（6类）', '1.配线形式:综合考虑；
2.导线型号、规格:网络线（6类）；
3.其它:穿线、编号、焊压接线端子及相关配件安装；
4.线路测试及完成该项工作的其他一切未尽事宜。', 'm', 1.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-029', '水电工', '网络线（超6类）', '1.配线形式:综合考虑；
2.导线型号、规格:网络线（超6类）；
3.其它:穿线、编号、焊压接线端子及相关配件安装；
4.线路测试及完成该项工作的其他一切未尽事宜。', 'm', 1.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-030', '水电工', '电话线', '1.配线形式:综合考虑；
2.规格型号:电话线；
3.工作内容:穿引线、扫管、涂滑石粉、穿线、编号、接焊包头。
4.线路测试及完成该项工作的其他一切未尽事宜。', 'm', 0.79, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-031', '水电工', '有线电视线', '1.配线形式:综合考虑；
2.规格型号:有线电视线；
3.工作内容:穿引线、扫管、涂滑石粉、穿线、编号、接焊包头。
4.线路测试及完成该项工作的其他一切未尽事宜。', 'm', 1.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-032', '水电工', '电力电缆单芯 电缆截面≤6mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：单芯 电缆截面≤6mm2', 'm', 2.62, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-033', '水电工', '电力电缆单芯 电缆截面≤10mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：单芯 电缆截面≤10mm2', 'm', 2.62, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-034', '水电工', '电力电缆单芯 电缆截面≤35mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：单芯 电缆截面≤35mm2', 'm', 5.03, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-035', '水电工', '电力电缆单芯 电缆截面≤70mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：单芯 电缆截面≤70mm2', 'm', 7.04, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-036', '水电工', '电力电缆单芯 电缆截面≤120mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：单芯 电缆截面≤120mm2', 'm', 10.3, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-037', '水电工', '电力电缆单芯 电缆截面≤185mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：单芯 电缆截面≤185mm2', 'm', 13.38, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-038', '水电工', '电力电缆单芯 电缆截面≤240mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：单芯 电缆截面≤240mm2', 'm', 16.28, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-039', '水电工', '电力电缆单芯 电缆截面≤400mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：单芯 电缆截面≤400mm2', 'm', 27.54, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-040', '水电工', '电力电缆二、三、四芯 电缆截面≤6mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：三芯 电缆截面≤6mm2', 'm', 3.92, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-041', '水电工', '电力电缆二、三、四芯 电缆截面≤10mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：三芯 电缆截面≤10mm2', 'm', 3.92, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-042', '水电工', '电力电缆二、三、四芯 电缆截面≤35mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：三芯 电缆截面≤35mm2', 'm', 7.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-043', '水电工', '电力电缆二、三、四芯 电缆截面≤70mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：三芯 电缆截面≤70mm2', 'm', 10.51, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-044', '水电工', '电力电缆二、三、四芯 电缆截面≤120mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：三芯 电缆截面≤120mm2', 'm', 15.38, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-045', '水电工', '电力电缆二、三、四芯 电缆截面≤185mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：三芯 电缆截面≤185mm2', 'm', 19.97, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-046', '水电工', '电力电缆二、三、四芯 电缆截面≤240mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：三芯 电缆截面≤240mm2', 'm', 24.3, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-047', '水电工', '电力电缆二、三、四芯 电缆截面≤400mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：三芯 电缆截面≤400mm2', 'm', 41.1, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-048', '水电工', '电力电缆五芯 电缆截面≤6mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤6mm2', 'm', 5.1, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-049', '水电工', '电力电缆五芯 电缆截面≤10mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤10mm2', 'm', 5.1, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-050', '水电工', '电力电缆五芯 电缆截面≤35mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤35mm2', 'm', 9.76, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-051', '水电工', '电力电缆五芯 电缆截面≤70mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤70mm2', 'm', 13.66, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-052', '水电工', '电力电缆五芯 电缆截面≤120mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤120mm2', 'm', 19.99, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-053', '水电工', '电力电缆五芯 电缆截面≤185mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤185mm2', 'm', 25.96, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-054', '水电工', '电力电缆五芯 电缆截面≤240mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤240mm2', 'm', 31.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-055', '水电工', '电力电缆五芯 电缆截面≤400mm2', '1.名称：铜芯电力电缆
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤400mm2', 'm', 53.42, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-056', '水电工', '刚性/柔性矿物质电力电缆单芯、二芯 电缆截面≤4mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求；
3.规格：单芯、二芯 电缆截面≤4mm2', 'm', 1.7, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-057', '水电工', '刚性/柔性矿物质电力电缆单芯、二芯 电缆截面≤10mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求；
3.规格：单芯、二芯 电缆截面≤10mm2', 'm', 2.15, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-058', '水电工', '刚性/柔性矿物质电力电缆单芯、二芯 电缆截面≤35mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求；
3.规格：单芯、二芯 电缆截面≤35mm2', 'm', 5.47, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-059', '水电工', '刚性/柔性矿物质电力电缆单芯、二芯 电缆截面≤70mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求；
3.规格：单芯、二芯 电缆截面≤70mm2', 'm', 9.61, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-060', '水电工', '刚性/柔性矿物质电力电缆单芯、二芯 电缆截面≤150mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求；
3.规格：单芯、二芯 电缆截面≤150mm2', 'm', 11.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-061', '水电工', '刚性/柔性矿物质电力电缆单芯、二芯 电缆截面≤240mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求；
3.规格：单芯、二芯 电缆截面≤240mm2', 'm', 15.06, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-062', '水电工', '刚性/柔性矿物质电力电缆单芯、二芯 电缆截面≤300mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求；
3.规格：单芯、二芯 电缆截面≤300mm2', 'm', 17.49, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-063', '水电工', '刚性/柔性矿物质电力电缆单芯、二芯 电缆截面≤400mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求；
3.规格：单芯、二芯 电缆截面≤400mm2', 'm', 23.06, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-064', '水电工', '刚性/柔性矿物质电力电缆三芯、四芯 电缆截面≤4mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求
3.规格：三芯、四芯 电缆截面≤4mm2', 'm', 3.05, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-065', '水电工', '刚性/柔性矿物质电力电缆三芯、四芯 电缆截面≤10mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求
3.规格：三芯、四芯 电缆截面≤10mm2', 'm', 5.69, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-066', '水电工', '刚性/柔性矿物质电力电缆三芯、四芯 电缆截面≤35mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求
3.规格：三芯、四芯 电缆截面≤35mm2', 'm', 10.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-067', '水电工', '刚性/柔性矿物质电力电缆三芯、四芯 电缆截面≤70mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求
3.规格：三芯、四芯 电缆截面≤70mm2', 'm', 13.32, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-068', '水电工', '刚性/柔性矿物质电力电缆三芯、四芯 电缆截面≤150mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求
3.规格：三芯、四芯 电缆截面≤150mm2', 'm', 23.77, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-069', '水电工', '刚性/柔性矿物质电力电缆三芯、四芯 电缆截面≤240mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求
3.规格：三芯、四芯 电缆截面≤240mm2', 'm', 26.78, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-070', '水电工', '刚性/柔性矿物质电力电缆五芯 电缆截面≤4mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤4mm2', 'm', 3.96, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-071', '水电工', '刚性/柔性矿物质电力电缆五芯 电缆截面≤10mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤10mm2', 'm', 7.39, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-072', '水电工', '刚性/柔性矿物质电力电缆五芯 电缆截面≤35mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤35mm2', 'm', 13.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-073', '水电工', '刚性/柔性矿物质电力电缆五芯 电缆截面≤70mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤70mm2', 'm', 17.32, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-074', '水电工', '刚性/柔性矿物质电力电缆五芯 电缆截面≤150mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤150mm2', 'm', 30.9, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-075', '水电工', '刚性/柔性矿物质电力电缆五芯 电缆截面≤240mm2', '1.名称：刚性/柔性矿物绝缘铜芯电力电缆；
2.型号：满足图纸要求
3.规格：五芯 电缆截面≤240mm2', 'm', 34.82, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-076', '水电工', '控制电缆电缆截面≤6芯', '1.名称：控制电缆 铜芯2.型号：满足图纸要求3.规格：电缆截面≤6芯', 'm', 2.43, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-077', '水电工', '控制电缆电缆截面≤14芯', '1.名称：控制电缆 铜芯2.型号：满足图纸要求3.规格：电缆截面≤14芯', 'm', 2.99, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-078', '水电工', '控制电缆电缆截面≤24芯', '1.名称：控制电缆 铜芯2.型号：满足图纸要求3.规格：电缆截面≤24芯', 'm', 3.96, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-079', '水电工', '吊灯', '1.名称:吊灯（装饰性吊灯按实际计算）
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 24.22, '大型吊灯，按实际另行报价');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-080', '水电工', '吸顶灯', '1.名称:吸顶灯
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 17.54, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-081', '水电工', '座灯头', '1.名称:座灯头
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 6.66, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-082', '水电工', '筒灯', '1.名称:筒灯
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 16.55, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-083', '水电工', '射灯', '1.名称:射灯
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 16.55, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-084', '水电工', '轨道射灯', '1.名称:轨道射灯
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 16.55, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-085', '水电工', '灯带', '1.名称:灯带
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', 'm', 4.13, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-086', '水电工', '线型洗墙灯', '1.名称:线型洗墙灯
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', 'm', 16.55, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-087', '水电工', '小夜灯', '1.名称:小夜灯
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 6.97, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-088', '水电工', '单管荧光灯', '1.名称:单管荧光灯/LED T5支架（含光源）
2.安装方式:综合考虑
3.工作内容:开箱清点、测位、划线、打眼埋螺栓、支架制作、安装、灯具拼装固定、挂装饰部件、接焊线包头、灯具追位、系统调试等；
4.完成该项工作的其他一切未尽事宜。', '个', 18.23, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-089', '水电工', '双管荧光灯', '1.名称:双管荧光灯（含光源）
2.安装方式:综合考虑
3.工作内容:开箱清点、测位、划线、打眼埋螺栓、支架制作、安装、灯具拼装固定、挂装饰部件、接焊线包头、灯具追位、系统调试等；
4.完成该项工作的其他一切未尽事宜。', '个', 22.84, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-090', '水电工', '三管荧光灯', '1.名称:三管荧光灯
2.安装方式:综合考虑
3.工作内容:开箱清点、测位、划线、打眼埋螺栓、支架制作、安装、灯具拼装固定、挂装饰部件、接焊线包头、灯具追位、系统调试等；
4.完成该项工作的其他一切未尽事宜。', '个', 25.55, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-091', '水电工', '嵌入式单管荧光灯', '1.名称:单管荧光灯
2.安装方式:综合考虑
3.工作内容:开箱清点、测位、划线、打眼埋螺栓、支架制作、安装、灯具拼装固定、挂装饰部件、接焊线包头、灯具追位、系统调试等；
4.完成该项工作的其他一切未尽事宜。', '个', 21.15, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-092', '水电工', '嵌入式双管荧光灯', '1.名称:双管荧光灯
2.安装方式:综合考虑
3.工作内容:开箱清点、测位、划线、打眼埋螺栓、支架制作、安装、灯具拼装固定、挂装饰部件、接焊线包头、灯具追位、系统调试等；
4.完成该项工作的其他一切未尽事宜。', '个', 33.94, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-093', '水电工', '嵌入式三管荧光灯', '1.名称:三管荧光灯
2.安装方式:综合考虑
3.工作内容:开箱清点、测位、划线、打眼埋螺栓、支架制作、安装、灯具拼装固定、挂装饰部件、接焊线包头、灯具追位、系统调试等；
4.完成该项工作的其他一切未尽事宜。', '个', 41.88, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-094', '水电工', '嵌入式四管荧光灯', '1.名称:四管荧光灯
2.安装方式:综合考虑
3.工作内容:开箱清点、测位、划线、打眼埋螺栓、支架制作、安装、灯具拼装固定、挂装饰部件、接焊线包头、灯具追位、系统调试等；
4.完成该项工作的其他一切未尽事宜。', '个', 50.26, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-095', '水电工', '格栅灯盘', '1.名称:格栅灯盘（尺寸600*600及以上）；
2.组装方式:成品现场安装、系统调试；
3.完成该项工作的其他一切未尽事宜。', '个', 23.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-96', '水电工', '应急格栅灯盘', '1名称：应急格栅灯盘
2规格型号：13W（紧凑型荧光灯）
3满足质量验收规范', '个', 23.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-97', '水电工', 'LED长条灯（1200*100mm）', '1.名称：LED长条灯                     
2.规格型号：1200*100            
3.安装方式：吸顶安装', '个', 33.94, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-98', '水电工', '集成吊顶灯', '1.名称:集成吊顶灯
2.安装方式:综合考虑
3.工作内容:开箱清点、测位、划线、打眼埋螺栓、支架制作、安装、灯具拼装固定、挂装饰部件、接焊线包头、灯具追位、系统调试等；
4.完成该项工作的其他一切未尽事宜。', '个', 33.94, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-99', '水电工', '安全出口灯', '1.名称:安全出口灯；
2.组装方式:成品现场安装、系统调试；
3.完成该项工作的其他一切未尽事宜。', '个', 11.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-100', '水电工', '疏散走道指示灯（自带蓄电池）', '1.名称:疏散走道指示灯（自带蓄电池）；
2.组装方式:成品现场安装、系统调试；
3.完成该项工作的其他一切未尽事宜。', '个', 11.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-101', '水电工', '双头应急灯', '1.名称：双头应急灯
2.规格：自带蓄电池
3.安装形式：综合考虑', '个', 26.45, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-102', '水电工', '壁灯', '1.名称：壁灯（装饰性壁灯按实际计算）
2.规格、型号：满足图纸要求
3.安装形式：墙壁式', '个', 16.94, '大型壁灯，按实际另行报价');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-103', '水电工', '卫生间排气扇', '1.名称:卫生间排气扇
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 27.86, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-104', '水电工', '浴霸', '1.名称:浴霸
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 41.89, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-105', '水电工', '厨房凉霸', '1.名称:厨房凉霸
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 41.89, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-106', '水电工', '壁扇', '1.名称:壁扇
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 42.24, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-107', '水电工', '声光报警器', '1.名称:声光报警器
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 48.92, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-108', '水电工', '紧急报警按钮', '1.名称:紧急报警按钮
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 7.94, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-109', '水电工', '电表安装', '1.名称:电表安装
2.型号及规格:综合考虑；
3.安装方式:综合考虑；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '套', 51.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-110', '水电工', '动力配电箱-落地式', '1.名称：配电箱
2.规格：综合考虑
3.基础形式、材质、规格：综合考虑
4.安装方式：落地式', '台', 320.05, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-111', '水电工', '配电箱 (半周长m以内) 0.5', '1.名称:配电箱
2.规格型号:半周长 0.5m以内；
3.安装方式:综合考虑嵌入式、悬挂式', '台', 132.07, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-112', '水电工', '配电箱 (半周长m以内) 1.0', '1.名称:配电箱
2.规格型号:半周长 1.0m以内；
3.安装方式:综合考虑嵌入式、悬挂式', '台', 158.67, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-113', '水电工', '配电箱 (半周长m以内) 1.5', '1.名称:配电箱
2.规格型号:半周长 1.5m以内；
3.安装方式:综合考虑嵌入式、悬挂式', '台', 202.93, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-114', '水电工', '配电箱 (半周长m以内) 2.5', '1.名称:配电箱
2.规格型号:半周长 2.5m以内；
3.安装方式:综合考虑嵌入式、悬挂式', '台', 246.93, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-115', '水电工', 'LEB箱', '1.名称：LEB等电位端子箱
2.主材形式：乙供自报价
3.包括内容：包括LEB及所有附件等完成所需一切内容', '台', 17.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-116', '水电工', '多媒体箱体', '1名称:户内多媒体箱
2主材形式:乙供自报价
3包括内容:包括箱体及所有附件、封堵（含防火封堵）、支架及油漆等完成所需一切内容。', '台', 105.65, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-117', '水电工', '弱电箱', '1.名称：弱电箱
2.材质：综合考虑
3.规格：综合考虑
4.安装形式：暗装', '台', 105.65, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-118', '水电工', 'T接箱', '1.名称：电缆T接箱
2.材质：钢质
3.规格：按周长综合考虑。
4.安装方式：端子接线安装，不区分明、暗装', '台', 79.88, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-119', '水电工', '单位单控开关220V 10A', '1.名称:单位单控开关
2.型号及规格:86型 10A220V
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-120', '水电工', '双位单控开关220V 10A', '1.名称:双位单控开关
2.型号及规格:86型 10A220V
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-121', '水电工', '三位单控开关220V 10A', '1.名称:三位单控开关
2.型号及规格:86型 10A220V
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-122', '水电工', '四联单控开关220V 10A', '1.名称:四联单控开关
2.型号及规格:86型 10A220V
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-123', '水电工', '单位双控开关220V 10A', '1.名称:单位双控开关
2.型号及规格:86型 10A220V
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-124', '水电工', '双位双控开关220V 10A', '1.名称:双位双控开关
2.型号及规格:86型 10A220V
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-125', '水电工', '声控(红外线感应)延时开关', '1.名称:声控(红外线感应)延时开关
2.型号及规格:按设计要求
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-126', '水电工', '多功能轻触(红外感应)延时开关', '1.名称:多功能轻触(红外感应)延时开关
2.型号及规格:按设计要求
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-127', '水电工', '风扇调速开关', '1.名称:风扇调速开关
2.型号及规格:按设计要求
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-128', '水电工', '紫外线灯开关(含专用小箱）', '1.名称:紫外线灯开关(含专用小箱） 
2.型号及规格:按设计要求
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-129', '水电工', '二三极插座220V 10A', '1.名称:二三极插座
2.型号及规格:86型 10A220V
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-130', '水电工', '空调插座220V 16A', '1.名称:空调插座
2.型号及规格:86型 
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.94, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-131', '水电工', '防水带开关热水器插座220V 16A', '1.名称:防水带开关热水器插座
2.型号及规格:86型 
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-132', '水电工', '防水带开关二三极插座220V 10A', '1.名称:防水带开关二三极插座
2.型号及规格:86型 
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-133', '水电工', '剃须插座220V 10A', '1.名称:剃须插座
2.型号及规格:86型 
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-134', '水电工', '带开关二三插座220V 10A', '1.名称:带开关二三插座
2.型号及规格:86型 
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-135', '水电工', '电视插座', '1.名称:电视插座
2.型号及规格:86型 
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-136', '水电工', '网线插座', '1.名称:网线插座
2.型号及规格:86型 
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-137', '水电工', '电话插座', '1.名称:电话插座
2.型号及规格:86型 
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-138', '水电工', 'WIFI控制面板（带网络插口）地插', '1.名称:WIFI控制面板（带网络插口）地插
2.型号、规格:综合考虑
3.其他:按钮安装、接线、调试', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-139', '水电工', '音箱插座', '1.名称:音箱插座
2.型号及规格:86型 
3.安装方式:暗装
4.包括系统调试但不限于施工文件、设计规范要求完成的其它工作内容', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-140', '水电工', '单相三极插座', '1.名称:单相三极插座
2.安装方式:嵌入式
3.型号:10A、16A
4.工作内容:开箱清点、测位、划线、打眼埋螺栓、支架制作、安装、灯具拼装固定、挂装饰部件、接焊线包头等5.完成该项工作的其他一切未尽事宜。', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-141', '水电工', '单相USB二三极插座', '1.名称:单相USB二三极插座
2.安装方式:嵌入式
3.型号:10A、16A
4.工作内容:开箱清点、测位、划线、打眼埋螺栓、支架制作、安装、灯具拼装固定、挂装饰部件、接焊线包头等5.完成该项工作的其他一切未尽事宜。', '个', 7.59, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-142', '水电工', '等电位接线盒（卫生间）', '1.名称:等电位接线盒
2.本体安装
3.包括将金属龙头、金属管道、金属五金件、淋浴支架等连接至等电位接线盒；
4.完成该项工作的其他一切未尽事宜。', '个', 17.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-143', '水电工', '门铃按钮', '1.名称:门铃按钮
2.型号及规格:86型 ；
3.安装方式:暗装；
4.工程内容:安装及系统调试；
5.完成该项工作的其他一切未尽事宜。', '个', 10.4, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-144', '水电工', '空白面板（用于开关插座位）', '1.名称：空白面板
2.规格：按图纸要求', '个', 0.92, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-145', '水电工', '不锈钢冷、热水管DN15', '1.安装部位:室内
2.介质:给水
3.材质、规格:DN15
4.连接形式:热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 13.71, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-146', '水电工', '不锈钢冷、热水管DN20', '1.安装部位:室内
2.介质:给水
3.材质、规格:DN20
4.连接形式:热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 15.08, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-147', '水电工', '不锈钢冷、热水管DN25', '1.安装部位:室内
2.介质:给水
3.材质、规格:DN25
4.连接形式:热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 16.33, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-148', '水电工', '不锈钢冷、热水管DN32', '1.安装部位:室内
2.介质:给水
3.材质、规格:DN32
4.连接形式:热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 17.03, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-149', '水电工', '不锈钢冷、热水管DN40', '1.安装部位:室内
2.介质:给水
3.材质、规格:DN40
4.连接形式:热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 18.52, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-150', '水电工', '不锈钢冷、热水管DN50', '1.安装部位:室内
2.介质:给水
3.材质、规格:DN50
4.连接形式:热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 19.93, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-151', '水电工', '不锈钢冷、热水管DN65', '1.安装部位:室内
2.介质:给水
3.材质、规格:DN65
4.连接形式:热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 23.3, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-152', '水电工', 'PP-R冷、热给水管DN15', '1.安装部位:室内
2.介质:PP-R冷、热给水管
3.材质、规格:DN15
4.连接形式:DN15 1.6MPa 冷水热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 10.35, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-153', '水电工', 'PP-R冷、热给水管DN20', '1.安装部位:室内
2.介质:PP-R冷、热给水管
3.材质、规格:DN20
4.连接形式:1.6MPa 冷水热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 10.93, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-154', '水电工', 'PP-R冷、热给水管DN25', '1.安装部位:室内
2.介质:PP-R冷、热给水管
3.材质、规格:DN25
4.连接形式:1.6MPa 冷水热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 12.65, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-155', '水电工', 'PP-R冷、热给水管DN32', '1.安装部位:室内
2.介质:PP-R冷、热给水管
3.材质、规格:DN32
4.连接形式:1.6MPa 冷水热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 12.65, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-156', '水电工', 'PP-R冷、热给水管DN40', '1.安装部位:室内
2.介质:PP-R冷、热给水管
3.材质、规格:DN40
4.连接形式:1.6MPa 冷水热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 12.9, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-157', '水电工', 'PP-R冷、热给水管DN50', '1.安装部位:室内
2.介质:PP-R冷、热给水管
3.材质、规格:DN50
4.连接形式:1.6MPa 冷水热熔连接
5.压力试验及吹、洗设计要求:保压、水压试验、水消毒及冲洗
6.完成该项工作的管件安装及其他一切未尽事宜', 'm', 14.51, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-158', '水电工', '保温管DN15', '1.绝热材料品种:橡塑保温
2.绝热厚度:综合考虑
3.管径:DN15
4.完成该项工作的其他一切未尽事宜', 'm', 0.92, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-159', '水电工', '保温管DN20', '1.绝热材料品种:橡塑保温
2.绝热厚度:综合考虑
3.管径:DN20
4.完成该项工作的其他一切未尽事宜', 'm', 0.92, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-160', '水电工', '保温管DN25', '1.绝热材料品种:橡塑保温
2.绝热厚度:综合考虑
3.管径:DN25
4.完成该项工作的其他一切未尽事宜', 'm', 1.84, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-161', '水电工', '保温管DN32', '1.绝热材料品种:橡塑保温
2.绝热厚度:综合考虑
3.管径:DN32
4.完成该项工作的其他一切未尽事宜', 'm', 2.05, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-162', '水电工', 'UPVC塑料排水管De50', '1.安装部位:室内
2.材质、规格:UPVC排水管 De50 壁厚按国家规定
3.输送介质:排水
4.连接方式:粘接
5.包括系统调试、管件安装但不限于招标文件、设计规范要求完成的其它工作内容', 'm', 11.72, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-163', '水电工', 'UPVC塑料排水管De75', '1.安装部位:室内
2.材质、规格:UPVC排水管 De75 壁厚按国家规定
3.输送介质:排水
4.连接方式:粘接
5.包括系统调试、管件安装但不限于招标文件、设计规范要求完成的其它工作内容', 'm', 13.57, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-164', '水电工', 'UPVC塑料排水管De110', '1.安装部位:室内
2.材质、规格:UPVC排水管 De100 壁厚按国家规定
3.输送介质:排水
4.连接方式:粘接
5.包括系统调试、管件安装但不限于招标文件、设计规范要求完成的其它工作内容', 'm', 16.33, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-165', '水电工', 'UPVC塑料排水管De160', '1.安装部位:室内
2.材质、规格:UPVC排水管 De160 壁厚按国家规定
3.输送介质:排水
4.连接方式:粘接
5.包括系统调试、管件安装但不限于招标文件、设计规范要求完成的其它工作内容', 'm', 25.88, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-166', '水电工', '铸铁排水管DN50', '1.安装部位：室内/室外
2.介质：排水
3.材质、规格：铸铁管 DN50
4.连接形式：综合考虑', 'm', 26.14, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-167', '水电工', '铸铁排水管DN75', '1.安装部位：室内/室外
2.介质：排水
3.材质、规格：铸铁管 DN75
4.连接形式：综合考虑', 'm', 31.64, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-168', '水电工', '铸铁排水管DN100', '1.安装部位：室内/室外
2.介质：排水
3.材质、规格：铸铁管 DN100
4.连接形式：综合考虑', 'm', 43.2, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-169', '水电工', '铸铁排水管DN150', '1.安装部位：室内/室外
2.介质：排水
3.材质、规格：铸铁管 DN150
4.连接形式：综合考虑', 'm', 46.96, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-170', '水电工', '置物架', '1.名称:置物架；
2.组装方式:成品现场安装；
3.完成该项工作的其他一切未尽事宜。', '个', 12.54, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-171', '水电工', '纸巾架', '1.名称:纸巾架；
2.组装方式:成品现场安装；
3.完成该项工作的其他一切未尽事宜。', '个', 12.54, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-172', '水电工', '电热毛巾架', '1.名称:电热毛巾架；
2.组装方式:成品现场安装；
3.完成该项工作的其他一切未尽事宜。', '个', 21.2, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-173', '水电工', '毛巾杆安装', '1.名称:安装
2.安装方式:不限
3.完成该项工作的其他一切未尽事宜', '个', 16.31, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-174', '水电工', '挂钩', '1.名称:挂钩
2.型号、规格:综合考虑
3.完成该项工作的其他一切未尽事宜。', '个', 9.79, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-175', '水电工', '不锈钢扶手', '1.名称:不锈钢扶手；
2.组装方式:成品现场安装；
3.完成该项工作的其他一切未尽事宜。', '个', 12.65, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-176', '水电工', '干手器', '1.名称:干手器
2.组装方式:成品现场安装；
3.完成该项工作的其他一切未尽事宜。', '个', 23.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-177', '水电工', '洗衣机龙头', '1.名称:洗衣机龙头
2.组装方式:成品现场安装；
3.完成该项工作的其他一切未尽事宜。', '个', 6.33, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-178', '水电工', '普通水龙头', '1.名称:普通水龙头
2.组装方式:成品现场安装；
3.完成该项工作的其他一切未尽事宜。', '个', 10.34, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-179', '水电工', '台下盆', '1.名称:台下盆；
2.组装方式:成品现场安装含角阀；
3.完成该项工作的其他一切未尽事宜。', '个', 51.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-180', '水电工', '立柱盆（角式）', '1.名称:立柱盆（角式）；
2.组装方式:成品现场安装含角阀；
3.完成该项工作的其他一切未尽事宜。', '个', 51.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-181', '水电工', '面盆龙头', '1.品牌、型号：详见材料表； 
2.安装所需之一切软管、下水管、角阀等辅材；
3.辅材含下水管，不含软管及角阀', '个', 17.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-182', '水电工', '蹲便器', '1.品牌、型号：详见材料表； 
2.安装所需之一切软管、下水管、角阀等辅材；软管、角阀为甲指乙供。
3.含蹲便器脚踏阀安装', '套', 63.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-183', '水电工', '坐便器带低水箱及配件', '1.名称:卫生间坐便器带低水箱及配件
2.组装方式:成品现场安装含角阀；
3.完成该项工作的其他一切未尽事宜。', '套', 63.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-184', '水电工', '厨盆-双盆', '1.名称:厨盆-双盆
2.组装方式:成品现场安装含角阀；
3.完成该项工作的其他一切未尽事宜。', '个', 51.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-185', '水电工', '单槽厨盆', '1.名称:单槽厨盆
2.组装方式:成品现场安装含角阀；
3.完成该项工作的其他一切未尽事宜。', '个', 51.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-186', '水电工', '厨盆龙头', '1.名称:厨盆龙头；
2.组装方式:成品现场安装；
3.完成该项工作的其他一切未尽事宜。', '个', 17.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-187', '水电工', '壁挂式感应式小便器', '1.名称:壁挂式感应式小便器；
2.组装方式:成品现场安装；
3.完成该项工作的其他一切未尽事宜。', '套', 63.25, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-188', '水电工', '淋浴器', '1.名称:卫生间沐浴器
2.组装方式:成品现场安装；
3.完成该项工作的其他一切未尽事宜。', '套', 54.44, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-189', '水电工', '拖把池', '1.名称:拖把池
2.组装方式:成品现场安装；
3.完成该项工作的其他一切未尽事宜。', '个', 51.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-190', '水电工', '浴缸', '1.名称:浴缸
2.组装方式:成品现场安装；
3.完成该项工作的其他一切未尽事宜。', '个', 120.75, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-191', '水电工', '金属地漏 DN50', '1.名称:金属地漏
2.规格;DN50
3.完成该项工作的其他一切未尽事宜', '个', 11.51, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-192', '水电工', '金属地漏 DN75', '1.名称:金属地漏
2.规格;DN75
3.完成该项工作的其他一切未尽事宜', '个', 12.19, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-193', '水电工', '金属地漏 DN100', '1.名称:金属地漏
2.规格;DN100
3.完成该项工作的其他一切未尽事宜', '个', 15.81, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-194', '水电工', '塑料地漏 DN50', '1.名称:塑料地漏
2.规格;DN50
3.完成该项工作的其他一切未尽事宜', '个', 6.99, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-195', '水电工', '塑料地漏 DN75', '1.名称:塑料地漏
2.规格;DN75
3.完成该项工作的其他一切未尽事宜', '个', 8.8, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-196', '水电工', '塑料地漏 DN100', '1.名称:塑料地漏
2.规格;DN100
3.完成该项工作的其他一切未尽事宜', '个', 15.15, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-197', '水电工', '塑料地漏 DN150', '1.名称:塑料地漏
2.规格;DN150
3.完成该项工作的其他一切未尽事宜', '个', 23.91, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-198', '水电工', 'PVC/金属地面扫除口DN50', '1.名称:PVC/金属地面扫除口
2.规格;DN50
3.完成该项工作的其他一切未尽事宜', '个', 6.99, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-199', '水电工', 'PVC/金属地面扫除口DN75', '1.名称:PVC/金属地面扫除口
2.规格;DN75
3.完成该项工作的其他一切未尽事宜', '个', 8.8, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-200', '水电工', 'PVC/金属地面扫除口DN100', '1.名称:PVC/金属地面扫除口
2.规格;DN100
3.完成该项工作的其他一切未尽事宜', '个', 9.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-201', '水电工', '水表DN15', '1.安装部位(室内/室外)：室内/室外
2.型号、规格：DN15
3.连接形式：螺纹连接', '个', 7.07, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-202', '水电工', '水表DN20', '1.安装部位(室内/室外)：室内/室外
2.型号、规格：DN20
3.连接形式：螺纹连接', '个', 7.07, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-203', '水电工', '水表DN25', '1.安装部位(室内/室外)：室内/室外
2.型号、规格：DN25
3.连接形式：螺纹连接', '个', 8.67, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-204', '水电工', '水表DN32', '1.安装部位(室内/室外)：室内/室外
2.型号、规格：DN32
3.连接形式：螺纹连接', '个', 10.42, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-205', '水电工', '水表DN40', '1.安装部位(室内/室外)：室内/室外
2.型号、规格：DN40
3.连接形式：螺纹连接', '个', 19.3, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-206', '水电工', '水表DN50', '1.安装部位(室内/室外)：室内/室外
2.型号、规格：DN50
3.连接形式：螺纹连接', '个', 19.3, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-207', '水电工', '水表DN65', '1.安装部位(室内/室外)：室内/室外
2.型号、规格：DN65
3.连接形式：螺纹连接', '个', 52.89, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-208', '水电工', '水表DN80', '1.安装部位(室内/室外)：室内/室外
2.型号、规格：DN80
3.连接形式：螺纹连接', '个', 60.17, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-209', '水电工', '水表DN100', '1.安装部位(室内/室外)：室内/室外
2.型号、规格：DN100
3.连接形式：螺纹连接', '个', 74.66, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-210', '水电工', '螺纹阀DN15', '1.类型：螺纹闸阀/止回阀/截止阀
2.材质：钢质/铜质
3.规格、压力等级：DN15
4.连接形式：螺纹连接', '个', 9.78, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-211', '水电工', '螺纹阀DN20', '1.类型：螺纹闸阀/止回阀/截止阀
2.材质：钢质/铜质
3.规格、压力等级：DN20
4.连接形式：螺纹连接', '个', 10.78, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-212', '水电工', '螺纹阀DN25', '1.类型：螺纹闸阀/止回阀/截止阀
2.材质：钢质/铜质
3.规格、压力等级：DN25
4.连接形式：螺纹连接', '个', 12.21, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-213', '水电工', '螺纹阀DN32', '1.类型：螺纹闸阀/止回阀/截止阀
2.材质：钢质/铜质
3.规格、压力等级：DN32
4.连接形式：螺纹连接', '个', 14.66, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-214', '水电工', '螺纹阀DN40', '1.类型：螺纹闸阀/止回阀/截止阀
2.材质：钢质/铜质
3.规格、压力等级：DN40
4.连接形式：螺纹连接', '个', 26.22, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-215', '水电工', '螺纹阀DN50', '1.类型：螺纹闸阀/止回阀/截止阀
2.材质：钢质/铜质
3.规格、压力等级：DN50
4.连接形式：螺纹连接', '个', 26.94, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-216', '水电工', '集成卫浴安装费', '1.部位:卫生间；
2.含集成卫浴的墙板、防水底盘、天棚、洁具照明五金等（界面划分按进场后技术交底文件为准）', '套', 632.5, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-217', '水电工', '电气管线-户内', '户内辅材相关材料及附件（具体此价适用时议价后确认）', 'm2', 45.0, '以单方面积计算');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-218', '水电工', '给排水管道及附件-户内', '户内辅材相关材料及附件（具体此价适用时议价后确认）', 'm2', 15.0, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-219', '水电工', '凿槽、刨沟及修复', '1.结构形式:综合考虑
2.工程内容:综合考虑开槽深度、宽度；综合考虑线管槽及水管槽；含沟槽填补、恢复、抹灰及挂网。
3.完成该项工作的其他一切未尽事宜', '米', 17.63, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-220', '水电工', '开孔DN50-100', '1.名称:开孔含封堵
2.安装方式:不限
3.完成该项工作的其他一切未尽事宜', '个', 33.68, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-221', '水电工', '开孔DN50以下', '1.名称:开孔含封堵
2.安装方式:不限
3.完成该项工作的其他一切未尽事宜', '个', 24.13, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-222', '水电工', '砖墙底盒剔洞及修补', '1.名称：砖墙底盒开槽及修补2.规格：86*86', '个', 3.22, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-223', '水电工', '混凝土墙底盒剔洞及修补', '1.名称：混凝土墙底盒开槽及修补
2.规格：86*86', '个', 4.14, '');
INSERT INTO benchmark_items (trade_team, internal_code, work_type, item_name, spec, unit, unit_price, remark) VALUES ('机电班组', 'JD-224', '水电工', '卫生间等电位连接', '1.名称:卫生间等电位连接
 2.施工范畴：卫生间等电位端子盒（不含盒）后与卫生间金属器具、杆件的等电位连接导线及线管，并负责接入等电位端子盒
3.满足设计及规范相关技术要求。
4.以卫生间内等电位端子箱的套数计算', '套', 55.66, '');

COMMIT;
