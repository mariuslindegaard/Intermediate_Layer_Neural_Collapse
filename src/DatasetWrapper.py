import os
import warnings

import torch
import torch.nn.functional
from torchvision import datasets, transforms  # , models
from torch.utils.data import DataLoader  # , Subset

from typing import Optional, Dict, Tuple

# TODO(marius): Verify whether shuffling of data is needed


class DatasetWrapper:
    train_loader: DataLoader
    test_loader: DataLoader
    input_batch_shape: torch.Size
    target_batch_shape: torch.Size
    data_id: str
    is_one_hot: bool
    num_classes: int
    batch_size: int
    num_workers: int = 1

    data_download_dir = 'datasets'

    def __init__(self, data_cfg: dict, *args, **kwargs):
        """Init the dataset with given id"""
        self.data_id = data_cfg['dataset-id']
        self.batch_size = data_cfg['batch-size']
        self.num_workers = data_cfg.get('num-workers', min(16, len(os.sched_getaffinity(0))))

        id_mapping = {
            'cifar10': DatasetWrapper.cifar10,
            'mnist': DatasetWrapper.mnist,
            'cifar100': DatasetWrapper.cifar100,
            'imagenet': DatasetWrapper.imagenet,
            'stl10': DatasetWrapper.stl10,
            'svhn': DatasetWrapper.svhn
        }

        if not self.data_id.lower() in id_mapping.keys():
            raise NotImplementedError(f"Dataset with id '{self.data_id}' is not implemented. "
                                      f"Id must be one of \n{id_mapping.keys()}")

        # Prepeare datset
        train_data, test_data = id_mapping[self.data_id.lower()](self, data_cfg, *args, **kwargs)

        self.train_loader = DataLoader(train_data, batch_size=self.batch_size, num_workers=self.num_workers, shuffle=True)
        self.test_loader = DataLoader(test_data, batch_size=self.batch_size, num_workers=self.num_workers)

        tmp_inputs, tmp_targets = next(iter(self.train_loader))
        self.input_batch_shape = tmp_inputs.size()
        self.target_batch_shape = tmp_targets.size()

        # self._check_mean_std()

    def svhn(self, data_cfg: Optional[Dict] = None, download=True):
        if 'do-augmentation' not in data_cfg.keys():
            warnings.warn("Parameter 'do-augmentation' not specified in Data in config file. Defaulting to 'False'")
        do_augmentation = data_cfg.get('do-augmentation', False)

        normalize = transforms.Normalize(mean=[0.4377, 0.4438, 0.4728],
                                         std=[0.1980, 0.2010, 0.1970])

        test_tx = transforms.Compose([
            transforms.ToTensor(),
            normalize
        ])
        if do_augmentation:
            raise NotImplementedError()
        else:
            train_tx = test_tx

        train_data = datasets.SVHN(root=self.data_download_dir, split='train', download=download, transform=train_tx)
        test_data = datasets.SVHN(root=self.data_download_dir, split='test', download=download, transform=test_tx)
        self.is_one_hot = False
        self.num_classes = 10

        return train_data, test_data

    def stl10(self, data_cfg: Optional[Dict] = None, download=True):
        if 'do-augmentation' not in data_cfg.keys():
            warnings.warn("Parameter 'do-augmentation' not specified in Data in config file. Defaulting to 'False'")
        do_augmentation = data_cfg.get('do-augmentation', False)

        # normalize = transforms.Normalize(mean=[-3*0.1489, -3*0.1466, -3*0.1355],
        #                                  std=[1/x for x in [0.2487, 0.2548, 0.2475]])
        normalize = transforms.Normalize(mean=[0.4467, 0.4398, 0.4066],
                                         std=[0.2603, 0.2566, 0.2713])

        test_tx = transforms.Compose([
            transforms.ToTensor(),
            normalize
        ])
        if do_augmentation:
            raise NotImplementedError()
        else:
            train_tx = test_tx

        train_data = datasets.STL10(root=self.data_download_dir, split='train', download=download, transform=train_tx)
        test_data = datasets.STL10(root=self.data_download_dir, split='test', download=download, transform=test_tx)
        self.is_one_hot = False
        self.num_classes = 10

        return train_data, test_data

    def cifar100(self, data_cfg: Optional[Dict] = None, download=True):
        """Cifar100 dataset"""
        train_tx, test_tx = self._cifar_transforms(data_cfg)

        train_data = datasets.CIFAR100(root=self.data_download_dir, train=True, download=download, transform=train_tx)
        test_data = datasets.CIFAR100(root=self.data_download_dir, train=False, download=download, transform=test_tx)
        self.is_one_hot = False
        self.num_classes = 100
        # self.input_shape = (32, 32, 3)

        return train_data, test_data

    def cifar10(self, data_cfg: Optional[Dict] = None, download=True):
        """Cifar10 dataset"""
        train_tx, test_tx = self._cifar_transforms(data_cfg)

        train_data = datasets.CIFAR10(root=self.data_download_dir, train=True, download=download, transform=train_tx)
        test_data = datasets.CIFAR10(root=self.data_download_dir, train=False, download=download, transform=test_tx)
        self.is_one_hot = False
        self.num_classes = 10
        # self.input_shape = (32, 32, 3)

        return train_data, test_data

    @staticmethod
    def _cifar_transforms(data_cfg: Optional[Dict] = None) -> Tuple[transforms.transforms.Compose, transforms.transforms.Compose]:
        """Get the train and test transforms for cifar dataset"""
        if 'do-augmentation' not in data_cfg.keys():
            warnings.warn("Parameter 'do-augmentation' not specified in Data in config file. Defaulting to 'False'")
        do_augmentation = data_cfg.get('do-augmentation', False)

        normalize = transforms.Normalize(mean=[x/255.0 for x in [125.3, 123.0, 113.9]],
                                         std=[x/255.0 for x in [63.0, 62.1, 66.7]])

        test_tx = transforms.Compose([
            transforms.ToTensor(),
            normalize
        ])
        if do_augmentation:
            train_tx = transforms.Compose([
                transforms.RandomCrop(32, padding=4),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(15),
                test_tx
            ])
        else:
            train_tx = test_tx

        return train_tx, test_tx

    def imagenet(self, data_cfg: Optional[Dict] = None, download=True):
        if 'do-augmentation' not in data_cfg.keys():
            warnings.warn("Parameter 'do-augmentation' not specified in Data in config file. Defaulting to 'False'")
        do_augmentation = data_cfg.get('do-augmentation', False)

        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                         std=[0.229, 0.224, 0.225])

        test_tx = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            normalize
        ])
        if do_augmentation:
            train_tx = transforms.Compose([
                transforms.RandomCrop(224),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                normalize,
            ])
        else:
            train_tx = test_tx

        train_data = datasets.ImageNet(root=self.data_download_dir, train=True, download=download, transform=train_tx)
        test_data = datasets.ImageNet(root=self.data_download_dir, train=False, download=download, transform=test_tx)
        self.is_one_hot = False
        self.num_classes = 1000

        return train_data, test_data

    def mnist(self, data_cfg: Optional[Dict] = None, download=True):
        """Mnist dataset"""
        assert not data_cfg.get('do-augmentation', False), "Data augmentation specified for MNIST but is not supported."

        im_size = 28
        padded_im_size = 32

        tx = transforms.Compose([transforms.Pad((padded_im_size - im_size) // 2), transforms.ToTensor(),
                                 transforms.Normalize(mean=[0.1307], std=[0.3081])])

        train_data = datasets.MNIST(root=self.data_download_dir, train=True, download=download, transform=tx)
        test_data = datasets.MNIST(root=self.data_download_dir, train=False, download=download, transform=tx)

        self.num_classes = 10
        self.is_one_hot = False
        # self.input_shape = (32, 32, 1)

        return train_data, test_data

    def _check_mean_std(self):
        """Check mean and std of the current dataset"""
        import tqdm
        tot = torch.zeros((3,))
        tot_sq = torch.zeros_like(tot)
        i = 0
        for batch, (inputs, targets) in enumerate(tqdm.tqdm(self.train_loader)):
            tot += torch.sum(inputs, dim=(0, 2, 3))
            tot_sq += torch.sum(inputs**2, dim=(0, 2, 3))
            i += inputs.shape.numel() // 3

        mean = tot/i
        std = torch.sqrt(tot_sq/i - mean**2)
        print(mean, std)
        return mean, std


def load_dataset_from_dict(data_cfg: dict, *args, **kwargs) -> DatasetWrapper:
    """Load the dataset"""
    wrapper = DatasetWrapper(data_cfg, *args, **kwargs)
    return wrapper


def load_dataset(dataset_id: str, batch_size: int, *args, **kwargs) -> DatasetWrapper:
    """Load the dataset"""
    return load_dataset_from_dict({'dataset-id': dataset_id, 'batch-size': batch_size})


def _test():
    return load_dataset_from_dict({'dataset-id': 'cifar10', 'batch-size': 128})


if __name__ == "__main__":
    _test()
