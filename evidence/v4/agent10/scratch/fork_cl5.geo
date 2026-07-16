SetFactory("OpenCASCADE");
Mesh.CharacteristicLengthMax = 0.005;
Box(1) = {0, 0, 0, 0.022, 0.006, 0.015};                       // base
Box(2) = {0, 0, 0.015, 0.006, 0.006, 0.06};                    // prong A
Box(3) = {0.016, 0, 0.015, 0.006, 0.006, 0.06};                 // prong B
BooleanUnion{ Volume{1}; Delete; }{ Volume{2,3}; Delete; }
Physical Volume("fork") = {1};
