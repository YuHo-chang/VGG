import torch
import torchvision
from torch import nn
from torch.utils.data import Dataset 
from torch.utils.data import DataLoader
from skimage import io
import csv
import os

VGG19 = [
        64,
        64,
        "M",
        128,
        128,
        "M",
        256,
        256,
        256,
        256.0,
        "M",
        512,
        512,
        512,
        512.0,
        "M",
        512,
        512,
        512,
        512.0,
        "M",
    ]

class VGG(nn.Module):
    def __init__(
        self,
        architecture,
        in_channels=3, 
        in_height=224, 
        in_width=224, 
        num_hidden=4096,
        num_classes=10
    ):
        super(VGG, self).__init__()
        self.in_channels = in_channels
        self.in_width = in_width
        self.in_height = in_height
        self.num_hidden = num_hidden
        self.num_classes = num_classes
        self.convs = self.init_convs(architecture)
        self.fcs = self.init_fcs(architecture)
        
    def forward(self, x):
        x = self.convs(x)
        x = x.reshape(x.size(0), -1)
        x = self.fcs(x)
        return x
    
    def init_fcs(self, architecture):
        pool_count = architecture.count("M")
        factor = (2 ** pool_count)
        if (self.in_height % factor) + (self.in_width % factor) != 0:
            raise ValueError(
                f"`in_height` and `in_width` must be multiples of {factor}"
            )
        out_height = self.in_height // factor
        out_width = self.in_width // factor
        last_out_channels = next(
            x for x in architecture[::-1] if type(x) == int
        )
        return nn.Sequential(
            nn.Linear(
                last_out_channels * out_height * out_width, 
                self.num_hidden),
            nn.ReLU(),
            nn.Dropout(p=0.5),
            nn.Linear(self.num_hidden, self.num_classes)
            # nn.ReLU(),
            # nn.Dropout(p=0.5),
            # nn.Linear(self.num_hidden, self.num_classes)
        )
    
    def init_convs(self, architecture):
        layers = []
        in_channels = self.in_channels
        
        for x in architecture:
            if type(x) == int:
                out_channels = x
                layers.extend(
                    [
                        nn.Conv2d(
                            in_channels=in_channels,
                            out_channels=out_channels,
                            kernel_size=(3, 3),
                            stride=(1, 1),
                            padding=(1, 1),
                        ),
                        nn.BatchNorm2d(out_channels),
                        nn.ReLU(),
                    ]
                )
                in_channels = x
            elif type(x) == float:
                out_channels = int(x)
                layers.extend(
                    [
                        nn.Conv2d(
                            in_channels=in_channels,
                            out_channels=out_channels,
                            kernel_size=(1, 1),
                            stride=(1, 1),
                        ),
                        nn.BatchNorm2d(out_channels),
                        nn.ReLU(),
                    ]
                )
                in_channels = int(x)
            else:
                layers.append(
                    nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2))
                )

        return nn.Sequential(*layers)

class SportLoader(Dataset):
    def __init__(self, img_list, transform=torchvision.transforms.ToTensor()):
        self.img_list = img_list  # imd_name list from csv file
        self.transform = transform
    
    def __len__(self):
        return len(self.img_list)

    def __getitem__(self, index):
        img_path = "dataset/test/" + self.img_list[index]
        img = io.imread(img_path)
        img = self.transform(img)
        return img, self.img_list[index]

test_img = os.listdir('dataset/test')
test_dataset = SportLoader(test_img)
test_loader = DataLoader(test_dataset, batch_size=64)

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model = torch.load("HW1_311554021.pt")
model.to(device)

test_img = []
test_predicted = []
with torch.no_grad():
    for images, img_path in test_loader:
        images = images.to(device)
        outputs = model(images)
        _, predicted = torch.max(outputs.data, 1)
        temp = predicted.cpu().numpy()
        test_predicted.extend(temp)
        test_img.extend(img_path)
        del images, outputs

with open("HW1_311554021.csv", 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["names", "label"])
    for i in range(len(test_img)):
        writer.writerow([test_img[i], test_predicted[i]])
    f.close()